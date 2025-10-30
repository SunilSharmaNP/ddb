import re
import requests
from bs4 import BeautifulSoup
import logging
import atexit

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
        atexit.register(self.close_session)

    def close_session(self):
        """Close the requests session to prevent resource leaks"""
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
                        video_info['title'] = title_text
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

    def get_download_link(self, url):
        """Get direct download link for DiskWala video"""
        try:
            file_id = self.extract_file_id(url)
            if not file_id:
                return None

            api_endpoints = [
                f"https://www.diskwala.com/api/file/{file_id}",
                f"https://www.diskwala.com/api/download/{file_id}",
                f"https://www.diskwala.com/api/video/{file_id}",
            ]

            for endpoint in api_endpoints:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    headers = self.session.headers.copy()
                    if self.api_key:
                        headers['Authorization'] = f'Bearer {self.api_key}'
                        headers['X-API-Key'] = self.api_key

                    response = self.session.get(endpoint, headers=headers, timeout=30)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"API response: {data}")

                            possible_keys = ['downloadUrl', 'download_url', 'url', 'videoUrl', 'video_url', 'file_url', 'link']
                            for key in possible_keys:
                                if key in data and data[key]:
                                    logger.info(f"Found download URL: {data[key]}")
                                    return data[key]

                            if 'data' in data and isinstance(data['data'], dict):
                                for key in possible_keys:
                                    if key in data['data'] and data['data'][key]:
                                        return data['data'][key]
                        except ValueError:
                            logger.debug(f"Endpoint {endpoint} returned non-JSON response")
                            continue

                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout on endpoint {endpoint}")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request error on endpoint {endpoint}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Endpoint {endpoint} failed: {e}")
                    continue

            logger.info("API endpoints failed, trying alternative methods")
            return self._get_download_link_alternative(url, file_id)

        except Exception as e:
            logger.error(f"Error getting download link: {e}", exc_info=True)
            return None

    def _get_download_link_alternative(self, url, file_id):
        """Alternative method to extract download link"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src:
                    logger.info(f"Found video source in HTML: {src}")
                    return src
            
            source_tags = soup.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    logger.info(f"Found source tag: {src}")
                    return src
            
            download_links = soup.find_all('a', href=True)
            for link in download_links:
                href = link.get('href', '')
                if 'download' in href.lower() or file_id in href:
                    logger.info(f"Found download link: {href}")
                    return href

            logger.warning("Could not find download link using alternative methods")
            return None

        except Exception as e:
            logger.error(f"Alternative method failed: {e}", exc_info=True)
            return None

    def download_video(self, url, output_path):
        """Download video from DiskWala to specified path"""
        try:
            download_url = self.get_download_link(url)

            if not download_url:
                logger.error("Could not extract download URL")
                return False

            if not download_url.startswith('http'):
                download_url = 'https://www.diskwala.com' + download_url

            logger.info(f"Downloading from: {download_url}")

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
