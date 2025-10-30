# 🚀 DiskWala Bot - VPS Deployment Guide (Hindi)

## VPS Setup Guide

### Step 1: VPS par login karein
```bash
ssh root@your-vps-ip
```

### Step 2: Updates install karein
```bash
apt update && apt upgrade -y
```

### Step 3: Docker install karein
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Step 4: Docker Compose install karein
```bash
apt install docker-compose -y
```

### Step 5: Bot files upload karein
```bash
# Apne local machine se VPS par files transfer karein
scp -r diskwala-bot/ root@your-vps-ip:/root/
```

Ya phir VPS par directly clone karein:
```bash
cd /root
git clone <your-repo-url> diskwala-bot
cd diskwala-bot
```

### Step 6: Environment variables set karein
```bash
cd /root/diskwala-bot
nano .env
```

File mein ye add karein:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
DISKWALA_API_KEY=
DOWNLOAD_DIR=./downloads
MAX_FILE_SIZE=2097152000
LOG_LEVEL=INFO
```

Save karein: `Ctrl + X`, phir `Y`, phir `Enter`

### Step 7: Bot start karein using Docker
```bash
docker-compose up -d
```

### Step 8: Bot logs check karein
```bash
docker-compose logs -f
```

### Step 9: Bot stop karein (agar zarurat ho)
```bash
docker-compose down
```

### Step 10: Bot restart karein
```bash
docker-compose restart
```

---

## Alternative: Systemd Service (Without Docker)

### Step 1: Python install karein
```bash
apt install python3.11 python3-pip -y
```

### Step 2: Bot dependencies install karein
```bash
cd /root/diskwala-bot
pip3 install python-telegram-bot requests aiohttp aiofiles python-dotenv beautifulsoup4 lxml
```

### Step 3: Service file banayein
```bash
nano /etc/systemd/system/diskwala-bot.service
```

Is content ko paste karein:
```ini
[Unit]
Description=DiskWala Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/diskwala-bot
EnvironmentFile=/root/diskwala-bot/.env
ExecStart=/usr/bin/python3 /root/diskwala-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 4: Service enable aur start karein
```bash
systemctl daemon-reload
systemctl enable diskwala-bot
systemctl start diskwala-bot
```

### Step 5: Status check karein
```bash
systemctl status diskwala-bot
```

### Step 6: Logs dekhein
```bash
journalctl -u diskwala-bot -f
```

### Useful Commands:
```bash
# Bot stop karein
systemctl stop diskwala-bot

# Bot restart karein
systemctl restart diskwala-bot

# Bot disable karein
systemctl disable diskwala-bot
```

---

## Bot Testing

1. Telegram par apne bot ko search karein
2. `/start` command bhejein
3. DiskWala video link bhejein:
   ```
   https://www.diskwala.com/app/68fcd53fa57987ab2711f591
   ```
4. Bot video download karke aapko bhej dega

---

## Troubleshooting

### Bot start nahi ho raha?
```bash
# Logs check karein
docker-compose logs

# Ya systemd ke liye
journalctl -u diskwala-bot -n 50
```

### Token error aa raha hai?
- `.env` file check karein
- `TELEGRAM_BOT_TOKEN` sahi hai ya nahi verify karein

### Memory/CPU issue?
```bash
# Resources check karein
docker stats

# System resources
htop
```

### Bot crash ho raha hai?
```bash
# Bot restart karein
docker-compose restart

# Fresh start
docker-compose down
docker-compose up -d
```

---

## Auto-start on Server Reboot

Docker method automatically server reboot par start ho jayega.

Systemd method ke liye ye already set hai `enable` command se.

---

## Bot Update Kaise Karein

### Docker method:
```bash
cd /root/diskwala-bot
git pull  # Ya naye files upload karein
docker-compose down
docker-compose build
docker-compose up -d
```

### Systemd method:
```bash
cd /root/diskwala-bot
git pull  # Ya naye files upload karein
systemctl restart diskwala-bot
```

---

## Security Tips

1. **Firewall enable karein:**
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

2. **Regular updates:**
```bash
apt update && apt upgrade -y
```

3. **Bot token safe rakhein** - kabhi bhi publicly share na karein

4. **Backup lein regularly**

---

Enjoy your DiskWala Downloader Bot! 🎉
