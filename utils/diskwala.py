import re
import requests
from bs4 import BeautifulSoup
import logging
import atexit
import asyncio
import json
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class DiskWalaDownloader:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.diskwala.com/'
        })
        self.playwright_browser = None
        atexit.register(self.close_session)

    def close_session(self):
        """Close the requests session and playwright browser to prevent resource leaks"""
        try:
            if self.session:
                self.session.close()
                logger.debug("Session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

    def extract_file_id(self, url):
        """Extract file ID from DiskWala URL"""
        patterns = [
            r'diskwala\.com/app/([a-zA-Z0-9]+)',
            r'diskwala\.com/file/([a-zA-Z0-9]+)',
            r'/app/([a-zA-Z0-9]+)',
            r'/file/([a-zA-Z0-9]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_video_info(self, url):
        """Get video information from DiskWala link"""
        try:
            file_id = self.extract_file_id(url)
            if not file_id:
                logger.error(f"Invalid DiskWala URL: {url}")
                return None

            logger.info(f"Extracted file ID: {file_id}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            video_info = {
                'file_id': file_id,
                'url': url,
                'title': 'DiskWala Video',
                'download_url': None
            }

            # Try to extract title from various sources
            title_selectors = [
                ('h6', {}),
                ('h5', {}),
                ('h4', {}),
                ('title', {}),
                ('meta', {'property': 'og:title'}),
                ('meta', {'name': 'title'}),
                ('div', {'class': 'video-title'}),
                ('span', {'class': 'file-name'})
            ]

            for tag_name, attrs in title_selectors:
                title_elem = soup.find(tag_name, attrs)
                if title_elem:
                    if tag_name == 'meta':
                        title_text = title_elem.get('content', '').strip()
                    else:
                        title_text = title_elem.text.strip()
                    
                    if title_text and len(title_text) > 2:
                        video_info['title'] = title_text[:100]  # Limit title length
                        logger.info(f"Found video title: {title_text}")
                        break

            logger.info(f"Video info: {video_info}")
            return video_info

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching video info from: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting video info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting video info: {e}", exc_info=True)
            return None

    async def _get_download_link_with_playwright(self, url: str, file_id: str) -> Optional[str]:
        """Use Playwright to extract download link from DiskWala"""
        try:
            from playwright.async_api import async_playwright
            
            logger.info("Using Playwright to extract download link...")
            
            async with async_playwright() as p:
                # Try to find system chromium executable
                import shutil
                chromium_path = shutil.which('chromium') or shutil.which('chromium-browser')
                
                # Launch browser in headless mode
                launch_options = {
                    'headless': True,
                    'args': [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--single-process'
                    ]
                }
                
                # Use system chromium if found, otherwise use Playwright's bundled browser
                if chromium_path:
                    logger.info(f"Using system Chromium at: {chromium_path}")
                    launch_options['executable_path'] = chromium_path
                else:
                    logger.info("Using Playwright's bundled Chromium")
                
                browser = await p.chromium.launch(**launch_options)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Track network requests to capture video URL
                video_urls = []
                
                async def handle_route(route, request):
                    """Intercept network requests"""
                    url = request.url
                    # Look for video/media URLs
                    if any(ext in url.lower() for ext in ['.mp4', '.mkv', '.avi', '.webm', '.m3u8']):
                        logger.info(f"Found potential video URL: {url}")
                        video_urls.append(url)
                    await route.continue_()
                
                await page.route('**/*', handle_route)
                
                # Navigate to DiskWala page
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait a bit for JavaScript to execute
                await asyncio.sleep(3)
                
                # Try to find video elements or download buttons
                try:
                    # Look for video elements
                    video_element = await page.query_selector('video')
                    if video_element:
                        src = await video_element.get_attribute('src')
                        if src:
                            logger.info(f"Found video element with src: {src}")
                            video_urls.append(src)
                    
                    # Look for source elements
                    source_elements = await page.query_selector_all('source')
                    for source in source_elements:
                        src = await source.get_attribute('src')
                        if src:
                            logger.info(f"Found source element with src: {src}")
                            video_urls.append(src)
                    
                    # Try to extract download URL from page content
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for download links in the HTML
                    for script in soup.find_all('script'):
                        if script.string:
                            # Search for URLs in JavaScript code
                            url_matches = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|mkv|avi|webm|m3u8)', script.string)
                            video_urls.extend(url_matches)
                
                except Exception as e:
                    logger.warning(f"Error extracting video from page: {e}")
                
                await browser.close()
                
                # Return the first valid video URL found
                if video_urls:
                    # Prefer URLs that look like direct downloads
                    for url in video_urls:
                        if 'cdn' in url.lower() or 'stream' in url.lower() or file_id in url:
                            logger.info(f"Selected video URL: {url}")
                            return url
                    # Return the first URL if no preferred one found
                    logger.info(f"Selected first video URL: {video_urls[0]}")
                    return video_urls[0]
                
                logger.warning("No video URLs found with Playwright")
                return None
                
        except ImportError:
            logger.error("Playwright not installed properly")
            return None
        except Exception as e:
            logger.error(f"Playwright extraction failed: {e}", exc_info=True)
            return None

    async def get_download_link(self, url):
        """Get direct download link for DiskWala video"""
        try:
            file_id = self.extract_file_id(url)
            if not file_id:
                return None

            # Method 1: Try direct API endpoints (fastest)
            logger.info("Trying direct API endpoints...")
            api_url = self._try_api_endpoints(file_id)
            if api_url:
                return api_url

            # Method 2: Try HTML scraping
            logger.info("Trying HTML scraping...")
            scraping_url = self._get_download_link_alternative(url, file_id)
            if scraping_url:
                return scraping_url

            # Method 3: Use Playwright (most reliable but slower)
            logger.info("Using Playwright browser automation...")
            try:
                # Use existing event loop
                playwright_url = await self._get_download_link_with_playwright(url, file_id)
                if playwright_url:
                    return playwright_url
            except Exception as e:
                logger.error(f"Playwright method failed: {e}", exc_info=True)

            logger.error("All methods failed to extract download link")
            return None

        except Exception as e:
            logger.error(f"Error getting download link: {e}", exc_info=True)
            return None

    def _try_api_endpoints(self, file_id: str) -> Optional[str]:
        """Try various API endpoints to get download URL"""
        api_endpoints = [
            f"https://www.diskwala.com/api/file/{file_id}",
            f"https://www.diskwala.com/api/download/{file_id}",
            f"https://www.diskwala.com/api/video/{file_id}",
            f"https://api.diskwala.com/file/{file_id}",
            f"https://api.diskwala.com/download/{file_id}",
        ]

        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")
                headers = self.session.headers.copy()
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'
                    headers['X-API-Key'] = self.api_key

                response = self.session.get(endpoint, headers=headers, timeout=15)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Try various possible keys
                        possible_keys = ['downloadUrl', 'download_url', 'url', 'videoUrl', 'video_url', 'file_url', 'link', 'streamUrl']
                        for key in possible_keys:
                            if key in data and data[key]:
                                logger.info(f"Found download URL from API: {data[key]}")
                                return data[key]

                        # Check nested data object
                        if 'data' in data and isinstance(data['data'], dict):
                            for key in possible_keys:
                                if key in data['data'] and data['data'][key]:
                                    return data['data'][key]
                    except ValueError:
                        continue

            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue

        return None

    def _get_download_link_alternative(self, url, file_id):
        """Alternative method to extract download link using HTML scraping"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src:
                    logger.info(f"Found video source in HTML: {src}")
                    return src
            
            # Look for source tags
            source_tags = soup.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    logger.info(f"Found source tag: {src}")
                    return src
            
            # Look for download links
            download_links = soup.find_all('a', href=True)
            for link in download_links:
                href = link.get('href', '')
                if 'download' in href.lower() or file_id in href:
                    logger.info(f"Found download link: {href}")
                    return href
            
            # Try to find video URLs in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for URLs in JavaScript
                    url_patterns = [
                        r'"(https?://[^"]+\.mp4[^"]*)"',
                        r"'(https?://[^']+\.mp4[^']*)'",
                        r'"(https?://[^"]+/stream/[^"]+)"',
                        r'"url":\s*"([^"]+)"',
                    ]
                    for pattern in url_patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            logger.info(f"Found URL in script: {matches[0]}")
                            return matches[0]

            logger.warning("Could not find download link using HTML scraping")
            return None

        except Exception as e:
            logger.error(f"Alternative method failed: {e}", exc_info=True)
            return None

    def download_video(self, url, output_path, download_url=None):
        """Download video from DiskWala to specified path
        
        Args:
            url: DiskWala URL (used if download_url not provided)
            output_path: Path to save the downloaded video
            download_url: Optional pre-extracted download URL to reuse
        """
        try:
            # Use provided download_url or extract it
            if not download_url:
                download_url = self.get_download_link(url)

            if not download_url:
                logger.error("Could not extract download URL")
                return False

            # Ensure URL is absolute
            if not download_url.startswith('http'):
                download_url = 'https://www.diskwala.com' + download_url

            logger.info(f"Downloading from: {download_url}")

            # Download the video
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_logged_mb = 0

            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                    logger.info("Downloaded video (size unknown)")
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            current_mb = downloaded // (1024 * 1024)
                            if current_mb > last_logged_mb and current_mb % 10 == 0:
                                progress = (downloaded / total_size) * 100
                                logger.info(f"Download progress: {progress:.1f}% ({current_mb} MB)")
                                last_logged_mb = current_mb

            logger.info(f"Download completed: {output_path} ({downloaded} bytes)")
            return True

        except requests.exceptions.Timeout:
            logger.error("Download timeout - connection too slow or file too large")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading video: {e}")
            return False
        except IOError as e:
            logger.error(f"File I/O error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading video: {e}", exc_info=True)
            return False
