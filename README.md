# 🎵 MusicApp — Deployment Guide

---

## STEP 1 — Create RDS (MySQL Database)

1. AWS Console → **RDS** → **Create database**
2. Engine: **MySQL 8.0**
3. Template: **Free tier**
4. DB identifier: `musicapp-db`
5. Master username: `admin`
6. Master password: `YourPassword123!` ← save this
7. Connectivity → Public access: **No**
8. Create new security group → name it `musicapp-rds-sg`
9. Click **Create database** → wait 5 mins
10. Copy the **Endpoint URL** → you will need it later

### Allow EC2 to access RDS:
1. EC2 → your instance → note its **Security Group name**
2. RDS → your database → **Connectivity** → click its security group
3. Inbound rules → Edit → Add rule:
   - Type: **MySQL/Aurora** (port 3306)
   - Source: select your **EC2 security group**
4. Save

---

## STEP 2 — Create S3 Bucket

1. AWS Console → **S3** → **Create bucket**
2. Bucket name: `musicapp-songs-yourname` ← must be globally unique
3. Region: `us-east-1`
4. Keep **Block all public access** ON
5. Click **Create bucket**

### Add CORS to S3 Bucket:
S3 → your bucket → **Permissions** → **CORS** → Edit → paste:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

---

## STEP 3 — Create IAM User (AWS Access Keys)

1. AWS Console → **IAM** → **Users** → **Create user**
2. Username: `musicapp-backend`
3. Attach policy: **AmazonS3FullAccess**
4. Create user → open the user → **Security credentials** → **Create access key**
5. Use case: **Application running outside AWS**
6. **Save Access Key ID and Secret Access Key** ← shown only once!

---

## STEP 4 — Launch EC2 Instance

1. AWS Console → **EC2** → **Launch instance**
2. Name: `musicapp-server`
3. AMI: **Amazon Linux 2023**
4. Instance type: `t2.micro` (free tier)
5. Key pair: Create new → download `.pem` file
6. Security group inbound rules:
   - SSH port **22** → My IP
   - HTTP port **80** → Anywhere (0.0.0.0/0)
7. Storage: 20 GB
8. Click **Launch** → copy the **Public IP**

---

## STEP 5 — SSH into EC2

```bash
chmod 400 musicapp-key.pem
ssh -i musicapp-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

---

## STEP 6 — Install Required Software

```bash
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx
sudo yum install -y mariadb105
```

---

## STEP 7 — Create the Database

```bash
mysql -h YOUR_RDS_ENDPOINT -u admin -p
```

Enter your RDS password when prompted, then run:

```sql
CREATE DATABASE musicapp;
exit;
```

---

## STEP 8 — Clone Your GitHub Repo

```bash
git clone https://github.com/YOUR_USERNAME/music-app.git
cd music-app
```

---

## STEP 9 — Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## STEP 10 — Install Python Packages

```bash
pip install -r backend/requirements.txt
pip install cryptography
```

---

## STEP 11 — Create .env File

```bash
vi backend/.env
```

Press `i` to start typing, then paste and fill in your real values:

```
DB_HOST=your-rds-endpoint.us-east-1.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=your-rds-master-password
DB_NAME=musicapp
DB_PORT=3306

S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY=your-iam-access-key
AWS_SECRET_KEY=your-iam-secret-key

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your16charapppassword

SECRET_KEY=any-long-random-string-minimum-30-characters
```

Press `Esc` → type `:wq` → press `Enter` to save.

---

### How to get Gmail App Password:
1. Go to **myaccount.google.com** → Security
2. Turn on **2-Step Verification**
3. Search **App Passwords** in search bar
4. Create one → name it `MusicApp`
5. Copy the 16-character password → paste it **without spaces**

### Secret Key Rules:
- Make it at least 30 characters long
- Can be anything random e.g. `x7k#mP9@qLnR5vT8wY1uZ3cA6bD0eF`
- **Never push it to GitHub**

---

## STEP 12 — Add load_dotenv to app.py

```bash
vi backend/app.py
```

Press `i`, go to the very top of the file and add these 2 lines right after all the imports:

```python
from dotenv import load_dotenv
load_dotenv()
```

Press `Esc` → type `:wq` → press `Enter` to save.

---

## STEP 13 — Initialize Database Tables

```bash
cd backend
python3 -c 'from app import init_db; init_db(); print("Database ready")'
cd ..
```

You should see: `Database ready`

---

## STEP 14 — Create Gunicorn Service

```bash
nano /etc/systemd/system/musicapp.service
```

Paste this exactly:

```
[Unit]
Description=MusicApp Flask Backend
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/music-app/backend
EnvironmentFile=/root/music-app/backend/.env
ExecStart=/root/music-app/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X` → `Y` → `Enter`

Then run:

```bash
mkdir -p /var/log/musicapp
sudo systemctl daemon-reload
sudo systemctl enable musicapp
sudo systemctl start musicapp
sudo systemctl status musicapp
```

You should see **active (running)** in green ✅

---

## STEP 15 — Configure Nginx

```bash
nano /etc/nginx/conf.d/musicapp.conf
```

Paste this (replace with your real EC2 public IP):

```nginx
server {
    listen 80;
    server_name YOUR_EC2_PUBLIC_IP;

    location / {
        root /root/music-app/frontend;
        index play.html;
        try_files $uri $uri/ /play.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        client_max_body_size 100M;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
}
```

Save: `Ctrl+X` → `Y` → `Enter`

Then run:

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

`nginx -t` must say **syntax is ok** before continuing ✅

---

## STEP 16 — Fix Permissions

```bash
chmod 755 /root
chmod -R 755 /root/music-app/frontend
```

---

## STEP 17 — Update API URL in Frontend

```bash
nano /root/music-app/frontend/config.js
```

Change line 2 to your EC2 public IP (no port number):

```javascript
const API_BASE = 'http://YOUR_EC2_PUBLIC_IP/api';
```

Save: `Ctrl+X` → `Y` → `Enter`

> ⚠️ Do NOT put `:5000` in this URL. Nginx handles the routing automatically.

---

## STEP 18 — Open Your App 🎉

Open your browser and go to:

```
http://YOUR_EC2_PUBLIC_IP/signup.html
```

---

## Useful Commands

```bash
# Check backend status
sudo systemctl status musicapp

# View backend errors live
sudo journalctl -u musicapp -f

# Restart backend
sudo systemctl restart musicapp

# Restart nginx
sudo systemctl restart nginx

# View nginx error log
sudo tail -f /var/log/nginx/error.log
```

---

## Update Code in Future

```bash
# On your LOCAL machine — push changes
git add .
git commit -m "describe your change"
git push origin main

# On EC2 — pull changes
cd ~/music-app
git pull origin main
sudo systemctl restart musicapp
```
