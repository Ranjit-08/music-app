# 🎵 MusicApp — Private Server Deployment Guide
## (2 Private EC2s + Internal Backend ALB + Public Frontend ALB)

---

## Architecture

```
           INTERNET (Users)
                │
                ▼
    ┌─────────────────────────┐
    │   Public Frontend ALB    │  ← Only public entry point
    │   (Internet-facing)      │    DNS: musicapp-frontend-alb-xxx.elb.amazonaws.com
    └─────────────────────────┘
                │ port 80
                ▼
    ┌─────────────────────────┐
    │   Frontend EC2 (PRIVATE) │  ← No public IP
    │   Nginx                  │    Serves HTML/CSS/JS
    └─────────────────────────┘
                │ /api/ only
                ▼
    ┌─────────────────────────┐
    │   Internal Backend ALB   │  ← Not reachable from internet
    │   (Internal)             │    DNS: internal-musicapp-backend-alb-xxx.elb.amazonaws.com
    └─────────────────────────┘
                │ port 80
                ▼
    ┌─────────────────────────┐
    │   Backend EC2 (PRIVATE)  │  ← No public IP
    │   Nginx + Gunicorn       │    Runs Flask API
    └─────────────────────────┘
           │              │
           ▼              ▼
       AWS RDS          AWS S3
     (MySQL DB)      (Music files)
```

### Request flow:
```
Browser → Public Frontend ALB → Frontend EC2 Nginx
  ├── GET /play.html        → returns static file
  └── POST /api/auth/login  → Internal Backend ALB → Backend EC2 Flask → RDS
```

---

## STEP 1 — AWS Prerequisites (RDS + S3 + IAM)

### Create RDS
1. RDS → Create database → MySQL 8.0 → Free tier
2. Identifier: `musicapp-db` | Username: `admin` | Password: save it
3. Public access: **No**
4. VPC: **Default VPC** (same as EC2s)
5. Note the **Endpoint URL**

### Create S3 Bucket
1. S3 → Create bucket → name: `musicapp-songs-yourname`
2. Region: `us-east-1` | Block public access: **ON**
3. Add CORS (Permissions → CORS → Edit):
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

### Create IAM User
1. IAM → Users → Create user → `musicapp-backend`
2. Attach: **AmazonS3FullAccess**
3. Security credentials → Create access key → save both keys

---

## STEP 2 — Create Security Groups

> Security groups control who can talk to whom.

### Frontend EC2 Security Group — `musicapp-frontend-sg`
| Type | Port | Source | Reason |
|------|------|--------|--------|
| HTTP | 80 | `musicapp-frontend-alb-sg` | Only ALB can send traffic |
| SSH  | 22 | Your IP (or SSM only) | For setup |

### Backend EC2 Security Group — `musicapp-backend-sg`
| Type | Port | Source | Reason |
|------|------|--------|--------|
| HTTP | 80 | `musicapp-backend-alb-sg` | Only Internal ALB can send traffic |
| SSH  | 22 | Your IP (or SSM only) | For setup |

### Frontend ALB Security Group — `musicapp-frontend-alb-sg`
| Type | Port | Source | Reason |
|------|------|--------|--------|
| HTTP | 80 | 0.0.0.0/0 | Open to internet |

### Backend ALB Security Group — `musicapp-backend-alb-sg`
| Type | Port | Source | Reason |
|------|------|--------|--------|
| HTTP | 80 | `musicapp-frontend-sg` | Only frontend EC2 can call backend |

### RDS Security Group — update existing
| Type | Port | Source | Reason |
|------|------|--------|--------|
| MySQL | 3306 | `musicapp-backend-sg` | Only backend EC2 accesses DB |

---

## STEP 3 — Launch 2 Private EC2 Instances

> Both instances will have NO public IP address.

### Frontend EC2
1. EC2 → Launch instance
2. Name: `musicapp-frontend`
3. AMI: **Amazon Linux 2023**
4. Instance type: `t2.micro`
5. Key pair: create or use existing
6. Network settings:
   - VPC: Default VPC
   - Subnet: any public subnet (needed for SSM/NAT access)
   - **Auto-assign public IP: DISABLE** ← private server
7. Security group: **musicapp-frontend-sg**
8. Launch

### Backend EC2
1. EC2 → Launch instance
2. Name: `musicapp-backend`
3. AMI: **Amazon Linux 2023**
4. Instance type: `t2.micro`
5. Key pair: same key pair
6. Network settings:
   - VPC: Default VPC
   - Subnet: any subnet
   - **Auto-assign public IP: DISABLE** ← private server
7. Security group: **musicapp-backend-sg**
8. Launch

> ### Connecting to Private EC2 (no public IP)
> You can NOT ssh directly. Use one of these methods:
>
> **Option A — AWS Systems Manager (SSM) — Recommended, free:**
> 1. Attach IAM role `AmazonSSMManagedInstanceCore` to both EC2 instances
> 2. EC2 Console → select instance → Connect → Session Manager → Connect
>
> **Option B — Bastion Host:**
> Launch a small t2.micro EC2 WITH a public IP in the same VPC
> SSH into bastion → SSH from bastion into private EC2

---

## STEP 4 — Enable SSM on EC2 Instances (for private access)

For each EC2:
1. Select instance → Actions → Security → Modify IAM role
2. Create new role → AWS service → EC2
3. Attach policy: **AmazonSSMManagedInstanceCore**
4. Also attach: **AmazonS3FullAccess** (for Backend EC2 only)
5. Save

Wait 2-3 minutes, then: EC2 → instance → Connect → Session Manager → Connect

---

## STEP 5 — Create Load Balancers

### 5A. Internal Backend ALB (create this FIRST — need its DNS for frontend nginx)

1. EC2 → Load Balancers → Create load balancer → **Application Load Balancer**
2. Name: `musicapp-backend-alb`
3. Scheme: **Internal** ← critical
4. VPC: Default VPC
5. Subnets: select **at least 2** different AZs
6. Security group: **musicapp-backend-alb-sg**
7. Listener: HTTP port 80
8. Target group: Create new
   - Name: `musicapp-backend-tg`
   - Type: Instances | Protocol: HTTP | Port: 80
   - Health check path: `/health`
9. Register targets → select **Backend EC2** → port 80 → Include as pending
10. Create
11. **Copy the Internal ALB DNS** → `internal-musicapp-backend-alb-xxx.us-east-1.elb.amazonaws.com`

### 5B. Public Frontend ALB

1. EC2 → Load Balancers → Create load balancer → **Application Load Balancer**
2. Name: `musicapp-frontend-alb`
3. Scheme: **Internet-facing** ← public
4. VPC: Default VPC
5. Subnets: select at least 2 AZs
6. Security group: **musicapp-frontend-alb-sg**
7. Listener: HTTP port 80
8. Target group: Create new
   - Name: `musicapp-frontend-tg`
   - Type: Instances | Protocol: HTTP | Port: 80
   - Health check path: `/health`
9. Register targets → select **Frontend EC2** → port 80
10. Create
11. **Copy the Public ALB DNS** → `musicapp-frontend-alb-xxx.us-east-1.elb.amazonaws.com`

---

## STEP 6 — Setup Backend EC2

Connect via SSM: EC2 → Backend instance → Connect → Session Manager

```bash
# Switch to root
sudo su -

# Install packages
yum update -y
yum install -y python3 python3-pip git nginx mariadb105

## Create the Database

```bash
mysql -h YOUR_RDS_ENDPOINT -u admin -p
```
Enter your RDS password when prompted, then run:

```sql
CREATE DATABASE musicapp;
exit;
```

---
# Clone repo
---
git clone https://github.com/YOUR_USERNAME/music-app.git
cd music-app

---
# Python environment
---
1. python3 -m venv venv
2. source venv/bin/activate
3. pip install -r backend/requirements.txt
4. pip install cryptography
```

### Create .env file
```bash
nano backend/.env
```

Paste and fill in your values:
```
DB_HOST=your-rds-endpoint.us-east-1.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=your-rds-password
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

SECRET_KEY=your-long-random-string-minimum-30-chars

# ← CRITICAL: Must match your Frontend Public ALB DNS
FRONTEND_URL=http://musicapp-frontend-alb-xxx.us-east-1.elb.amazonaws.com
APP_URL=http://musicapp-frontend-alb-xxx.us-east-1.elb.amazonaws.com
```

Save: `Ctrl+X` → `Y` → `Enter`

### Add load_dotenv to app.py
```bash
nano backend/app.py
```
At the very top after imports add:
```python
from dotenv import load_dotenv
load_dotenv()
```
Save and exit.

### Initialize database
```bash
cd backend
python3 -c 'from app import init_db; init_db(); print("Database ready")'
cd ..
```

### Create Gunicorn service
```bash
nano /etc/systemd/system/musicapp.service
```
Paste:
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

```bash
mkdir -p /var/log/musicapp
systemctl daemon-reload
systemctl enable musicapp
systemctl start musicapp
systemctl status musicapp
```

### Configure Backend Nginx
```bash
nano /etc/nginx/conf.d/musicapp.conf
```
Paste:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout    300;
        proxy_connect_timeout 300;
        client_max_body_size  100M;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
}
```
```bash
nginx -t
systemctl restart nginx
systemctl enable nginx
```

### Test backend health
```bash
curl http://localhost/health
# Should return: {"status": "ok"}
```

---

## STEP 7 — Setup Frontend EC2

Connect via SSM: EC2 → Frontend instance → Connect → Session Manager

```bash
sudo su -

# Install packages
yum update -y
yum install -y git nginx

# Clone repo
git clone https://github.com/YOUR_USERNAME/music-app.git
cd music-app
```

### Update config.js with your Frontend Public ALB DNS
```bash
nano frontend/config.js
```
Change line 1 to:
```javascript
const API_BASE = 'http://musicapp-frontend-alb-xxx.us-east-1.elb.amazonaws.com/api';
```
Save: `Ctrl+X` → `Y` → `Enter`

### Fix permissions
```bash
chmod 755 /root
chmod -R 755 /root/music-app/frontend
```

### Configure Frontend Nginx
```bash
nano /etc/nginx/conf.d/musicapp.conf
```
Paste (replace with your real Internal Backend ALB DNS):
```nginx
server {
    listen 80;
    server_name _;

    location / {
        root  /root/music-app/frontend;
        index play.html;
        try_files $uri $uri/ /play.html;
    }

    location /api/ {
        proxy_pass         http://internal-musicapp-backend-alb-xxx.us-east-1.elb.amazonaws.com;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout    300;
        proxy_connect_timeout 300;
        client_max_body_size  100M;
    }

    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
```
```bash
nginx -t
systemctl restart nginx
systemctl enable nginx
```

---

## STEP 8 — Test Everything

### From Backend EC2 terminal — test health:
```bash
curl http://localhost/health
# Expected: {"status": "ok"}
```

### From Frontend EC2 terminal — test Internal ALB reaches backend:
```bash
curl http://INTERNAL-BACKEND-ALB-DNS/health
# Expected: {"status": "ok"}
```

### From your browser — test the full app:
```
http://FRONTEND-PUBLIC-ALB-DNS/signup.html
```

### Full checklist:
- [ ] Signup page loads
- [ ] Can create account — OTP email arrives
- [ ] OTP verification works
- [ ] Login works
- [ ] Forgot password email has correct URL (not localhost)
- [ ] Reset password link opens and works
- [ ] Can upload a song
- [ ] Song plays in browser

---

## STEP 9 — Update Code in Future

```bash
# Local machine — push changes
git add .
git commit -m "your change"
git push origin main

# Frontend EC2 (via SSM)
sudo su -
cd ~/music-app
git pull origin main
systemctl restart nginx

# Backend EC2 (via SSM)
sudo su -
cd ~/music-app
git pull origin main
systemctl restart musicapp
```

---

## Quick Reference — What Goes Where

| Item | Frontend EC2 | Backend EC2 |
|------|:---:|:---:|
| HTML/CSS/JS files | ✅ | ❌ |
| config.js | ✅ | ❌ |
| app.py (Flask) | ❌ | ✅ |
| .env file | ❌ | ✅ |
| venv / Python | ❌ | ✅ |
| Gunicorn service | ❌ | ✅ |
| Nginx | ✅ | ✅ |
| RDS / S3 access | ❌ | ✅ |
| Public IP | ❌ | ❌ |
| Reachable from internet | Via ALB only | Via Internal ALB only |

---

## Backend .env Reference

```
DB_HOST          → RDS endpoint
DB_USER          → admin
DB_PASSWORD      → RDS master password
DB_NAME          → musicapp
DB_PORT          → 3306
S3_BUCKET        → your bucket name
S3_REGION        → us-east-1
AWS_ACCESS_KEY   → IAM access key
AWS_SECRET_KEY   → IAM secret key
MAIL_SERVER      → smtp.gmail.com
MAIL_PORT        → 587
MAIL_USERNAME    → your Gmail
MAIL_PASSWORD    → 16-char app password (no spaces)
SECRET_KEY       → 30+ char random string
FRONTEND_URL     → http://FRONTEND-PUBLIC-ALB-DNS   ← CORS
APP_URL          → http://FRONTEND-PUBLIC-ALB-DNS   ← Reset email link
```

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| Page not loading | `systemctl status nginx` on Frontend EC2 |
| API calls failing 502 | `systemctl status musicapp` on Backend EC2 |
| Backend ALB health check failing | `curl http://localhost/health` on Backend EC2 |
| Reset email has localhost link | Check `APP_URL` in backend `.env`, restart musicapp |
| CORS error in browser | Check `FRONTEND_URL` in `.env` exactly matches ALB DNS |
| Can't reach EC2 | Use SSM Session Manager in EC2 console |
| Songs not uploading | Check IAM keys and S3 bucket name in `.env` |
| OTP not arriving | Check Gmail app password in `.env` (no spaces) |

```bash
# Useful debug commands on Backend EC2
systemctl status musicapp
journalctl -u musicapp -f       # live backend logs
systemctl status nginx
tail -f /var/log/nginx/error.log
```


