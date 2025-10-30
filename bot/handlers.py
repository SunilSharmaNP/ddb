"""
DiskWala Video Downloader - bot/handlers.py (FIXED & COMPLETE)
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from utils.diskwala import DiskWalaDownloader
from config.settings import DOWNLOAD_DIR, MAX_FILE_SIZE
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize downloader (FIXED: no api_key parameter)
downloader = DiskWalaDownloader()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_message = f"""
🎬 **DiskWala Video Downloader Bot**

Namaste {user.first_name}! 👋

Main aapki madad karunga DiskWala se videos download karne mein.

**Kaise Use Karein:**

📌 Bas mujhe DiskWala video link bhejiye

📌 Main usse download karke aapko bhej dunga

**Commands:**

/start - Bot ko shuru karein
/help - Madad paayein
/about - Bot ke baare mein jaankaari

**Example Link:**

`https://www.diskwala.com/app/68fcd53fa57987ab2711f591`

Chalo shuru karte hain! Link bhejiye 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton("📖 Help", callback_data='help'),
         InlineKeyboardButton("ℹ️ About", callback_data='about')],
        [InlineKeyboardButton("📢 Support", url='https://t.me/DiskwalaTeam')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    logger.info(f"User {user.id} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **DiskWala Downloader - Help Guide**

**Kaise Use Karein:**

1️⃣ DiskWala se video ka link copy karein
2️⃣ Mujhe wo link bhejein
3️⃣ Main video download karke aapko bhej dunga

**Supported Links:**

✅ https://www.diskwala.com/app/[ID]
✅ https://diskwala.com/app/[ID]
✅ https://www.diskwala.com/file/[ID]

**Features:**

⚡ Fast downloading
📤 Direct upload to Telegram
🎥 High quality videos
📊 Progress updates

**Limitations:**

⚠️ Max file size: 2GB
⚠️ Only video files supported

**Contact:** @DiskwalaTeam

Enjoy! 🎉
"""
    
    if update.message:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_text = """
ℹ️ **About DiskWala Downloader Bot**

**Version:** 1.0.0

**Developer:** Custom Bot Development

**Language:** Python 🐍

**Purpose:**

Ye bot DiskWala platform se videos download karne ke liye banaya gaya hai.

**Technology Stack:**

• Python 3.11
• python-telegram-bot
• Async/Await
• Beautiful Soup
• Playwright

**Support:**

Kisi bhi problem ke liye @DiskwalaTeam se contact karein.

**Disclaimer:**

⚠️ Sirf apne videos ya jinke aapke paas permission hai unhe hi download karein. Copyright laws ka dhyan rakhein.

Made with ❤️ in India 🇮🇳
"""
    
    if update.message:
        await update.message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        await help_command(update, context)
    elif query.data == 'about':
        await about_command(update, context)


def is_diskwala_link(text: str) -> bool:
    """Check if text contains DiskWala link"""
    patterns = [
        r'https?://(?:www\.)?diskwala\.com/app/[a-zA-Z0-9]+',
        r'https?://(?:www\.)?diskwala\.com/file/[a-zA-Z0-9]+',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def extract_diskwala_link(text: str) -> str:
    """Extract DiskWala link from text"""
    patterns = [
        r'https?://(?:www\.)?diskwala\.com/app/[a-zA-Z0-9]+',
        r'https?://(?:www\.)?diskwala\.com/file/[a-zA-Z0-9]+',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages (FIXED: proper async/await)"""
    message = update.message
    text = message.text
    
    if not text or not is_diskwala_link(text):
        await message.reply_text(
            "❌ **Invalid Link!**\n\n"
            "Kripya valid DiskWala link bhejein.\n\n"
            "**Example:**\n"
            "`https://www.diskwala.com/app/68fcd53fa57987ab2711f591`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    diskwala_url = extract_diskwala_link(text)
    logger.info(f"Processing DiskWala URL: {diskwala_url} from user {message.from_user.id}")
    
    await message.chat.send_action(ChatAction.TYPING)
    
    status_msg = await message.reply_text(
        "🔍 **Processing...**\n\n"
        "Video information nikal raha hoon...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    output_path = None
    
    try:
        # FIXED: Proper async/await
        video_info = await downloader.get_video_info(diskwala_url)
        
        if not video_info or 'error' in video_info:
            await status_msg.edit_text(
                "❌ **Error!**\n\n"
                "Video information nahi mil payi. Link check karein.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await status_msg.edit_text(
            f"📥 **Downloading...**\n\n"
            f"**Title:** {video_info['title']}\n"
            f"Please wait...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await message.chat.send_action(ChatAction.RECORD_VIDEO)
        
        # Create download directory
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # FIXED: Proper async/await
        output_path = Path(DOWNLOAD_DIR) / f"{video_info['file_id']}.mp4"
        
        # FIXED: Proper async/await
        download_url = await downloader.get_download_link(diskwala_url)
        
        if not download_url:
            await status_msg.edit_text(
                "⚠️ **Download Link Nahi Mila**\n\n"
                "Possible reasons:\n"
                "• Video private hai\n"
                "• Link expired hai\n"
                "• DiskWala API issue\n\n"
                "Kripya link check karein ya Support se contact karein.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # FIXED: Proper async/await
        success = await downloader.download_video(diskwala_url, output_path)
        
        if not success or not output_path.exists():
            await status_msg.edit_text(
                "❌ **Download Failed!**\n\n"
                "Video download nahi ho payi. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        file_size = output_path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(
                f"❌ **File Too Large!**\n\n"
                f"File size: {file_size / (1024*1024):.1f} MB\n"
                f"Max allowed: {MAX_FILE_SIZE / (1024*1024):.0f} MB",
                parse_mode=ParseMode.MARKDOWN
            )
            
            try:
                output_path.unlink()
                logger.info(f"Removed oversized file: {output_path}")
            except Exception as e:
                logger.warning(f"Failed to remove oversized file: {e}")
            
            return
        
        await status_msg.edit_text(
            "📤 **Uploading to Telegram...**\n\n"
            "Please wait, uploading video...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await message.chat.send_action(ChatAction.UPLOAD_VIDEO)
        
        # Upload video
        with open(output_path, 'rb') as video_file:
            caption = (
                f"🎬 **{video_info['title']}**\n\n"
                f"📊 Size: {file_size / (1024*1024):.1f} MB\n\n"
                f"✅ Downloaded by DiskWala Downloader Bot"
            )
            
            await message.reply_video(
                video=video_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300
            )
        
        await status_msg.delete()
        
        # Cleanup
        try:
            output_path.unlink()
            logger.info(f"Successfully removed temporary file: {output_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {e}")
        
        logger.info(f"Successfully processed and sent video to user {message.from_user.id}")
    
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        
        try:
            await status_msg.edit_text(
                f"❌ **Error Occurred!**\n\n"
                f"Kuch galat ho gaya:\n`{str(e)[:100]}`\n\n"
                f"Please try again ya Support se contact karein.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as edit_error:
            logger.error(f"Failed to edit status message: {edit_error}")
        
        # Cleanup on error
        if output_path and output_path.exists():
            try:
                output_path.unlink()
                logger.info(f"Cleaned up file after error: {output_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file: {cleanup_error}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ **An error occurred!**\n\n"
                "Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")
