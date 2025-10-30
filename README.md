# 🎬 DiskWala Video Downloader Bot

Ek professional Telegram bot jo DiskWala se videos download karke aapko directly Telegram par bhejta hai.

## ✨ Features

- ⚡ **Fast Download**: DiskWala se high-speed video downloading
- 📤 **Direct Upload**: Videos seedha Telegram par upload hote hain
- 🎥 **High Quality**: Original quality mein videos milte hain
- 📊 **Progress Updates**: Real-time download/upload progress
- 🎯 **User Friendly**: Simple UI aur easy commands
- 🔒 **Secure**: Safe aur private downloads

## 🚀 Quick Start

### Requirements

- Python 3.11+
- Telegram Bot Token
- DiskWala API Key (optional)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd diskwala-downloader-bot
```

2. **Install dependencies**
```bash
pip install uv
uv pip install -e .
```

Or alternatively:
```bash
pip install python-telegram-bot requests aiohttp aiofiles python-dotenv beautifulsoup4 lxml
```

3. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` file and add your credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
DISKWALA_API_KEY=  # Optional - leave empty if you don't have one
```

4. **Run the bot**
```bash
python main.py
```

## 🐳 Docker Deployment

### Build Docker Image
```bash
docker build -t diskwala-bot .
```

### Run with Docker
```bash
docker run -d \
  --name diskwala-bot \
  --env-file .env \
  -v $(pwd)/downloads:/app/downloads \
  diskwala-bot
```

### Docker Compose
```bash
docker-compose up -d
```

## 📝 Bot Usage

1. **Start the bot**
   - Send `/start` command

2. **Send DiskWala link**
   - Copy video link from DiskWala
   - Send it to the bot
   - Bot will download and upload video

3. **Commands**
   - `/start` - Start the bot
   - `/help` - Get help
   - `/about` - About the bot

### Example Links

```
https://www.diskwala.com/app/68fcd53fa57987ab2711f591
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | Yes |
| `TELEGRAM_API_ID` | Telegram API ID from my.telegram.org | Yes |
| `TELEGRAM_API_HASH` | Telegram API Hash from my.telegram.org | Yes |
| `DISKWALA_API_KEY` | Your DiskWala API key (if available) | No |
| `DOWNLOAD_DIR` | Directory for temporary downloads | No |
| `MAX_FILE_SIZE` | Maximum file size in bytes (default: 2GB) | No |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/WARNING) | No |

## 🖥️ VPS Deployment

### 1. Using systemd

Create service file: `/etc/systemd/system/diskwala-bot.service`

```ini
[Unit]
Description=DiskWala Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bot
EnvironmentFile=/path/to/bot/.env
ExecStart=/usr/bin/python3 /path/to/bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable diskwala-bot
sudo systemctl start diskwala-bot
sudo systemctl status diskwala-bot
```

### 2. Using PM2

```bash
pm2 start main.py --name diskwala-bot --interpreter python3
pm2 save
pm2 startup
```

## 📂 Project Structure

```
diskwala-downloader-bot/
├── bot/
│   ├── __init__.py
│   └── handlers.py          # Bot command handlers
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration settings
├── utils/
│   ├── __init__.py
│   └── diskwala.py          # DiskWala downloader logic
├── downloads/               # Temporary download directory
├── main.py                  # Main bot entry point
├── pyproject.toml          # Python dependencies & project config
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
└── README.md              # This file
```

## 🛠️ Troubleshooting

### Bot not starting?
- Check if `TELEGRAM_BOT_TOKEN` is set correctly
- Verify Python version (3.11+ required)
- Check logs in `bot.log`

### Download failing?
- Verify DiskWala link is valid
- Check if video is not private
- Ensure internet connection is stable

### Upload failing?
- Check if file size is under 2GB
- Verify bot has enough disk space
- Check Telegram API limits

## ⚠️ Limitations

- Maximum file size: 2GB (Telegram limit)
- Only video files supported
- Download speed depends on DiskWala servers
- Some private videos may not work

## 📄 License

This project is for educational purposes only.

## 🙏 Disclaimer

- Sirf apne videos ya jinke aapke paas permission hai unhe hi download karein
- Copyright laws ka dhyan rakhein
- Bot creator kisi bhi misuse ke liye responsible nahi hai

## 💬 Support

- Telegram: @DiskwalaTeam
- Issues: Create an issue on GitHub

## 🔄 Updates

### Version 1.0.0
- Initial release
- Basic download functionality
- Telegram upload support
- Progress tracking
- Error handling

---

Made with ❤️ in India 🇮🇳
