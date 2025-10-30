import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
DISKWALA_API_KEY = os.getenv('DISKWALA_API_KEY')

DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 2000 * 1024 * 1024))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',') if os.getenv('ALLOWED_USERS') else []

BOT_ADMIN_IDS = [int(uid) for uid in os.getenv('BOT_ADMIN_IDS', '').split(',') if uid.strip().isdigit()]
