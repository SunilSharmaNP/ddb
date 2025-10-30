import re
import asyncio
import logging
import aiohttp
import aiofiles
from typing import Optional, Dict
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class DiskWalaDownloader:
    """Enhanced DiskWala video downloader with multiple extraction methods."""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.diskwala.com/',
            'Origin': 'https://www.diskwala.com'
        }
        
    async def get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
        
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            
    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from DiskWala URL."""
        patterns = [
            r'/app/([a-f0-9]+)',
            r'/file/([a-f0-9]+)',
            r'/watch/([a-f0-9]+)',
            r'/v/([a-f0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                logger.info(f"Extracted file ID: {file_id}")
                return file_id
        
        logger.error("Could not extract file ID from URL")
        return None
        
    async def get_video_info(self, url: str) -> Dict:
        """Get video information from URL."""
        file_id = self.extract_file_id(url)
        if not file_id:
            return {'error': 'Invalid URL'}
            
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try to get title
                title = soup.find('title')
                title_text = title.text if title else "DiskWala Video"
                
                logger.info(f"Found video title: {title_text}")
                
                return {
                    'file_id': file_id,
                    'url': url,
                    'title': title_text,
                    'download_url': None
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {'error': str(e)}
    
    async def try_api_endpoints(self, file_id: str) -> Optional[str]:
        """Try various API endpoints to get download URL."""
        session = await self.get_session()
        
        # List of potential API endpoints
        api_endpoints = [
            f'https://www.diskwala.com/api/files/{file_id}',
            f'https://www.diskwala.com/api/v1/files/{file_id}',
            f'https://www.diskwala.com/api/file/{file_id}',
            f'https://www.diskwala.com/api/download/{file_id}',
            f'https://api.diskwala.com/files/{file_id}',
            f'https://api.diskwala.com/v1/files/{file_id}',
            f'https://www.diskwala.com/api/file/info/{file_id}',
            f'https://www.diskwala.com/api/stream/{file_id}',
        ]
        
        logger.info("Trying direct API endpoints...")
        
        for endpoint in api_endpoints:
            try:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"✓ API endpoint worked: {endpoint}")
                            logger.info(f"Response data keys: {list(data.keys())}")
                            
                            # Look for download URL in various possible fields
                            url_fields = ['download_url', 'url', 'file_url', 'stream_url', 
                                        'video_url', 'link', 'src', 'source', 'path']
                            
                            for field in url_fields:
                                if field in data and data[field]:
                                    logger.info(f"✓ Found download URL in field '{field}'")
                                    return data[field]
                                    
                            # Check nested objects
                            if 'file' in data and isinstance(data['file'], dict):
                                for field in url_fields:
                                    if field in data['file']:
                                        return data['file'][field]
                                        
                            if 'data' in data and isinstance(data['data'], dict):
                                for field in url_fields:
                                    if field in data['data']:
                                        return data['data'][field]
                                        
                        except Exception as e:
                            logger.debug(f"Endpoint {endpoint} returned non-JSON")
                            
            except asyncio.TimeoutError:
                logger.debug(f"Timeout: {endpoint}")
            except Exception as e:
                logger.debug(f"Error trying {endpoint}: {type(e).__name__}")
                
        return None
    
    async def extract_with_playwright_enhanced(self, url: str, file_id: str) -> Optional[str]:
        """Enhanced Playwright method with network interception."""
        logger.info("Using enhanced Playwright browser automation...")
        
        captured_urls = []
        
        async def handle_route(route, request):
            """Intercept and log network requests."""
            url_req = request.url
            
            # Log potential video/file URLs
            if any(ext in url_req.lower() for ext in ['.mp4', '.mkv', '.avi', '.webm', '.m3u8', '.mpd']):
                logger.info(f"📹 Captured video URL: {url_req}")
                captured_urls.append(url_req)
            elif 'stream' in url_req.lower() or 'download' in url_req.lower() or 'file' in url_req.lower():
                if file_id in url_req or 'cdn' in url_req.lower():
                    logger.info(f"🔗 Captured potential URL: {url_req}")
                    captured_urls.append(url_req)
                    
            await route.continue_()
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    user_agent=self.headers['User-Agent'],
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Enable request interception
                await page.route('**/*', handle_route)
                
                logger.info(f"Navigating to {url}")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for potential video player to load
                    await asyncio.sleep(3)
                    
                    # Try to find and click play button
                    play_selectors = [
                        'button[aria-label*="play"]',
                        'button.play-button',
                        '.video-play-button',
                        '[class*="play"]',
                        'video'
                    ]
                    
                    for selector in play_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                logger.info(f"Found element: {selector}")
                                await element.click()
                                await asyncio.sleep(2)
                                break
                        except:
                            continue
                    
                    # Look for video elements and their sources
                    video_elements = await page.query_selector_all('video')
                    for video in video_elements:
                        src = await video.get_attribute('src')
                        if src:
                            logger.info(f"Found video src: {src}")
                            captured_urls.append(src)
                    
                    # Check for source tags
                    source_elements = await page.query_selector_all('source')
                    for source in source_elements:
                        src = await source.get_attribute('src')
                        if src:
                            logger.info(f"Found source src: {src}")
                            captured_urls.append(src)
                    
                    # Execute JavaScript to find video URLs
                    js_result = await page.evaluate("""
                        () => {
                            const urls = [];
                            
                            // Check all video elements
                            document.querySelectorAll('video').forEach(v => {
                                if (v.src) urls.push(v.src);
                                if (v.currentSrc) urls.push(v.currentSrc);
                            });
                            
                            // Check source elements
                            document.querySelectorAll('source').forEach(s => {
                                if (s.src) urls.push(s.src);
                            });
                            
                            // Check for any data attributes
                            document.querySelectorAll('[data-src], [data-video], [data-file]').forEach(el => {
                                const src = el.dataset.src || el.dataset.video || el.dataset.file;
                                if (src) urls.push(src);
                            });
                            
                            return urls;
                        }
                    """)
                    
                    if js_result:
                        logger.info(f"JavaScript found {len(js_result)} URLs")
                        captured_urls.extend(js_result)
                    
                    await asyncio.sleep(2)
                    
                except PlaywrightTimeout:
                    logger.warning("Page load timeout")
                finally:
                    await browser.close()
                
                # Return the first valid video URL found
                for captured_url in captured_urls:
                    if captured_url and any(ext in captured_url.lower() for ext in ['.mp4', '.mkv', '.avi', '.webm', 'm3u8']):
                        logger.info(f"✓ Successfully extracted video URL")
                        return captured_url
                
                # If no video file, return any captured URL with file_id
                for captured_url in captured_urls:
                    if file_id in captured_url:
                        logger.info(f"✓ Found URL containing file_id")
                        return captured_url
                
                if captured_urls:
                    logger.info(f"✓ Returning first captured URL")
                    return captured_urls[0]
                    
        except Exception as e:
            logger.error(f"Playwright enhanced method failed: {e}")
            
        return None
    
    async def get_download_link(self, url: str) -> Optional[str]:
        """
        Main method to get download link using multiple strategies.
        Returns the download URL or None if all methods fail.
        """
        file_id = self.extract_file_id(url)
        if not file_id:
            return None
        
        # Method 1: Try API endpoints
        logger.info("Method 1: Trying API endpoints...")
        download_url = await self.try_api_endpoints(file_id)
        if download_url:
            return download_url
        
        # Method 2: Enhanced Playwright with network interception
        logger.info("Method 2: Using enhanced Playwright...")
        download_url = await self.extract_with_playwright_enhanced(url, file_id)
        if download_url:
            return download_url
        
        logger.error("All methods failed to extract download link")
        logger.info("\\nSUGGESTION: DiskWala may require:")
        logger.info("1. User authentication")
        logger.info("2. Mobile app API (need to reverse engineer)")
        logger.info("3. Premium/paid access")
        
        return None
    
    async def download_video(self, url: str, output_path: Path, progress_callback=None) -> bool:
        """Download video from URL with progress tracking."""
        try:
            download_url = await self.get_download_link(url)
            if not download_url:
                return False
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status != 200:
                    logger.error(f"Download failed with status: {response.status}")
                    return False
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                async with aiofiles.open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            await progress_callback(downloaded, total_size, progress)
                
                logger.info(f"✓ Download completed: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False


# Helper functions for backward compatibility
async def extract_video_info(url: str) -> Dict:
    """Extract video information from DiskWala URL."""
    downloader = DiskWalaDownloader()
    try:
        return await downloader.get_video_info(url)
    finally:
        await downloader.close()


async def get_download_link(url: str) -> Optional[str]:
    """Get direct download link for DiskWala video."""
    downloader = DiskWalaDownloader()
    try:
        return await downloader.get_download_link(url)
    finally:
        await downloader.close()
