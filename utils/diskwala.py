import re
import requests
from bs4 import BeautifulSoup
import logging

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
            
            title_elem = soup.find('h6')
            if title_elem:
                video_info['title'] = title_elem.text.strip()
            
            logger.info(f"Video info: {video_info}")
            return video_info
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
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
                        data = response.json()
                        logger.info(f"API response: {data}")
                        
                        possible_keys = ['downloadUrl', 'download_url', 'url', 'videoUrl', 'video_url', 'file_url', 'link']
                        for key in possible_keys:
                            if key in data and data[key]:
                                logger.info(f"Found download URL: {data[key]}")
                                return data[key]
                        
                        if 'data' in data:
                            for key in possible_keys:
                                if key in data['data'] and data['data'][key]:
                                    return data['data'][key]
                
                except requests.exceptions.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            logger.info("Trying alternative method using third-party API")
            return self._get_download_link_alternative(url, file_id)
            
        except Exception as e:
            logger.error(f"Error getting download link: {e}")
            return None
    
    def _get_download_link_alternative(self, url, file_id):
        """Alternative method to extract download link"""
        try:
            third_party_apis = [
                f"https://api.diskwala.net/download?url={url}",
                f"https://thediskwala.com/api/download?link={url}",
            ]
            
            for api_url in third_party_apis:
                try:
                    logger.info(f"Trying third-party API: {api_url}")
                    response = self.session.get(api_url, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if 'download_url' in data or 'url' in data:
                            return data.get('download_url') or data.get('url')
                except:
                    continue
            
            logger.info("Attempting direct file URL construction")
            possible_cdn_patterns = [
                f"https://cdn.diskwala.com/files/{file_id}",
                f"https://s3.diskwala.com/{file_id}",
                f"https://diskwala-files.s3.amazonaws.com/{file_id}",
            ]
            
            for cdn_url in possible_cdn_patterns:
                try:
                    head_response = self.session.head(cdn_url, timeout=10)
                    if head_response.status_code == 200:
                        logger.info(f"Found working CDN URL: {cdn_url}")
                        return cdn_url
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Alternative method failed: {e}")
            return None
    
    def download_video(self, url, output_path):
        """Download video from DiskWala to specified path"""
        try:
            download_url = self.get_download_link(url)
            
            if not download_url:
                logger.error("Could not extract download URL")
                return False
            
            logger.info(f"Downloading from: {download_url}")
            
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:
                                logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Download completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return False
