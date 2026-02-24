# STEP 1 — AWS Setup (Do this first, before touching EC2)
Create RDS (MySQL Database)

AWS Console → RDS → Create database
Engine: MySQL 8.0
Template: Free tier
DB identifier: musicapp-db
Username: admin | Password: YourPassword123! ← save this
Connectivity → Public access: No
Create new security group: name it musicapp-rds-sg
Click Create database → wait 5 mins
Copy the Endpoint URL (you'll need it later)

# step-2 Create S3 Bucket

AWS Console → S3 → Create bucket
Bucket name: musicapp-songs-yourname (must be unique globally)
Region: us-east-1
Keep "Block all public access" ON
Create bucket

# Then add CORS — go to S3 → your bucket → Permissions → CORS → Edit and paste:
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]

# Create IAM User (AWS Keys for your app)

AWS Console → IAM → Users → Create user
Username: musicapp-backend
Attach policy: AmazonS3FullAccess
Create user → open the user → Security credentials → Create access key
Use case: Application running outside AWS
Save the Access Key ID and Secret Access Key — shown only once!

# Launch EC2
sudo yum update -y
sudo yum install -y python3 python3-pip python3-venv nginx git
yum install mariadb105-server -y

# create database
mysql -h database-1.czg8gc6gg0gv.us-east-1.rds.amazonaws.com -u admin -p
CREATE DATABASE musicapp;
exit;

# git clone 
 1. Clone
git clone https://github.com/YOUR_USERNAME/music-app.git
cd ~/music-app

 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

 3. Install packages (requirements.txt is inside backend/)
pip install -r backend/requirements.txt

 4. Create .env file
    vi .env
    paste the code from git
    ex:

DB_HOST=database-1.czg8gc6gg0gv.us-east-1.rds.amazonaws.com  (rds-endpoint)
DB_USER=admin
DB_PASSWORD=database-1 (master-password)
DB_NAME=musicapp
DB_PORT=3306
S3_BUCKET=your-music-app-bucket-23rdfeb (bucket-name)
S3_REGION=us-east-1 
AWS_ACCESS_KEY=AKIA3FLD2IFBHCES4H44   (accesskey  of your user)
AWS_SECRET_KEY=WrPUSeaEYGtUK6OGnf8etof8bQlY9W8Zb5AIzpq6  (secret access key of your user)
MAIL_SERVER=smtp.gmail.com (dont change)
MAIL_PORT=587 
MAIL_USERNAME=qintondecock@gmail.com   (email.id)
MAIL_PASSWORD=smvgngeiybqxegqh  (go to gmail--> security-sign in 2 step verification need to on --> search for the app password  --> give a name like music-app then create paste it without any soace)
SECRET_KEY=anylongrandomstringhere123!@#xyz


    
note:
It can be ANY random string you make up
SECRET_KEY=anylongrandomstringhere123!@#xyz     ← fine
SECRET_KEY=MyMusicApp2024!SuperSecret           ← fine
SECRET_KEY=x7k#mP9@qL2nR5vT8wY1uZ3cA6bD0eF    ← better (more random)
Two rules:
Make it long (at least 30 characters)
Never share it or push it to GitHub

# 5. Init database
cd backend
pip install cryptography
python3 -c 'from app import init_db; init_db(); print("Database ready")'
cd ..
# add musicapp service

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

mkdir -p /var/log/musicapp

sudo systemctl daemon-reload
sudo systemctl enable musicapp
sudo systemctl start musicapp
sudo systemctl status musicapp

# root inside 
nano /etc/nginx/conf.d/musicapp.conf
server {
    listen 80;
    server_name 54.82.18.108;

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

sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
#  Update API URL in frontend
cd frotend
vi frontend/config.js

change the url..
const API_BASE = 'http://backend-public-ip/api';

chmod 755 /root
chmod -R 755 /root/music-app/frontend
