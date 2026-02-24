from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
import pymysql
import boto3
import os
import jwt
import random
import string
import hashlib
import datetime
from functools import wraps
from botocore.exceptions import NoCredentialsError
import uuid

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-very-secret-key-change-me')

# MySQL (RDS)
DB_HOST     = os.environ.get('DB_HOST',     'your-rds-endpoint.rds.amazonaws.com')
DB_USER     = os.environ.get('DB_USER',     'admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'yourpassword')
DB_NAME     = os.environ.get('DB_NAME',     'musicapp')
DB_PORT     = int(os.environ.get('DB_PORT', 3306))

# S3
S3_BUCKET      = os.environ.get('S3_BUCKET',      'your-music-app-bucket')
S3_REGION      = os.environ.get('S3_REGION',      'us-east-1')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', '')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')

# Flask-Mail (SES or Gmail SMTP)
app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'yourapp@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'yourapp@gmail.com')

mail = Mail(app)

# ─── DATABASE HELPERS ──────────────────────────────────────────────────────────
def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_db():
    conn = get_db()
    with conn.cursor() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                email       VARCHAR(255) UNIQUE NOT NULL,
                password    VARCHAR(255) NOT NULL,
                name        VARCHAR(255) NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified    BOOLEAN DEFAULT FALSE
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                email      VARCHAR(255) NOT NULL,
                code       VARCHAR(10)  NOT NULL,
                expires_at DATETIME NOT NULL,
                used       BOOLEAN DEFAULT FALSE,
                INDEX idx_email (email)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                title       VARCHAR(255) NOT NULL,
                artist      VARCHAR(255) NOT NULL,
                album       VARCHAR(255),
                genre       VARCHAR(100),
                s3_key      VARCHAR(500) NOT NULL,
                cover_s3_key VARCHAR(500),
                duration    INT DEFAULT 0,
                file_size   BIGINT DEFAULT 0,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
    conn.close()

# ─── S3 CLIENT ─────────────────────────────────────────────────────────────────
def get_s3():
    return boto3.client(
        's3',
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# ─── JWT AUTH DECORATOR ────────────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data['user_id']
            request.user_email = data['email']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name     = data.get('name', '').strip()

    if not email or not password or not name:
        return jsonify({'error': 'All fields required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id FROM users WHERE email=%s", (email,))
            if c.fetchone():
                return jsonify({'error': 'Email already registered'}), 409

            hashed = hash_password(password)
            c.execute("INSERT INTO users (email, password, name, verified) VALUES (%s,%s,%s,FALSE)",
                      (email, hashed, name))
            user_id = c.lastrowid

            # Generate & store OTP
            otp = generate_otp()
            expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            c.execute("INSERT INTO otp_codes (email, code, expires_at) VALUES (%s,%s,%s)",
                      (email, otp, expires))

        # Send OTP email
        msg = Message('Verify your MusicApp account', recipients=[email])
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;background:#0f0f0f;color:#fff;border-radius:12px;">
            <h1 style="color:#7c3aed;">🎵 MusicApp</h1>
            <p>Hi {name}, welcome! Please verify your email.</p>
            <div style="background:#1e1e1e;padding:20px;border-radius:8px;text-align:center;margin:20px 0;">
                <p style="color:#999;margin:0 0 10px;">Your verification code</p>
                <h2 style="color:#7c3aed;font-size:36px;letter-spacing:10px;margin:0;">{otp}</h2>
            </div>
            <p style="color:#666;font-size:12px;">This code expires in 10 minutes.</p>
        </div>
        """
        mail.send(msg)
        return jsonify({'message': 'Signup successful. Check your email for verification code.', 'user_id': user_id}), 201
    finally:
        conn.close()


@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()
    code  = data.get('code', '').strip()

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT id FROM otp_codes
                WHERE email=%s AND code=%s AND used=FALSE AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
            """, (email, code))
            otp_row = c.fetchone()
            if not otp_row:
                return jsonify({'error': 'Invalid or expired code'}), 400

            c.execute("UPDATE otp_codes SET used=TRUE WHERE id=%s", (otp_row['id'],))
            c.execute("UPDATE users SET verified=TRUE WHERE email=%s", (email,))

            c.execute("SELECT id, email, name FROM users WHERE email=%s", (email,))
            user = c.fetchone()
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({'message': 'Email verified!', 'token': token, 'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}), 200
    finally:
        conn.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, email, name, password, verified FROM users WHERE email=%s", (email,))
            user = c.fetchone()
            if not user or user['password'] != hash_password(password):
                return jsonify({'error': 'Invalid email or password'}), 401
            if not user['verified']:
                return jsonify({'error': 'Email not verified. Please check your inbox.', 'needs_verify': True}), 403

        # Send login OTP
        otp = generate_otp()
        expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        with conn.cursor() as c:
            c.execute("INSERT INTO otp_codes (email, code, expires_at) VALUES (%s,%s,%s)",
                      (email, otp, expires))

        msg = Message('Your MusicApp login code', recipients=[email])
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;background:#0f0f0f;color:#fff;border-radius:12px;">
            <h1 style="color:#7c3aed;">🎵 MusicApp</h1>
            <p>Hi {user['name']}, your login code is:</p>
            <div style="background:#1e1e1e;padding:20px;border-radius:8px;text-align:center;margin:20px 0;">
                <h2 style="color:#7c3aed;font-size:36px;letter-spacing:10px;margin:0;">{otp}</h2>
            </div>
            <p style="color:#666;font-size:12px;">Expires in 10 minutes. If you didn't request this, ignore it.</p>
        </div>
        """
        mail.send(msg)
        return jsonify({'message': 'Login code sent to your email.'}), 200
    finally:
        conn.close()


@app.route('/api/auth/verify-login', methods=['POST'])
def verify_login():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()
    code  = data.get('code', '').strip()

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT id FROM otp_codes
                WHERE email=%s AND code=%s AND used=FALSE AND expires_at > NOW()
                ORDER BY id DESC LIMIT 1
            """, (email, code))
            otp_row = c.fetchone()
            if not otp_row:
                return jsonify({'error': 'Invalid or expired code'}), 400

            c.execute("UPDATE otp_codes SET used=TRUE WHERE id=%s", (otp_row['id'],))
            c.execute("SELECT id, email, name FROM users WHERE email=%s", (email,))
            user = c.fetchone()

            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({'token': token, 'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}), 200
    finally:
        conn.close()


@app.route('/api/auth/me', methods=['GET'])
@token_required
def me():
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id, email, name, created_at FROM users WHERE id=%s", (request.user_id,))
            user = c.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            return jsonify({'user': user}), 200
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#  MUSIC ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/songs/upload', methods=['POST'])
@token_required
def upload_song():
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio file required'}), 400

    audio_file = request.files['audio']
    title      = request.form.get('title', 'Untitled').strip()
    artist     = request.form.get('artist', 'Unknown').strip()
    album      = request.form.get('album', '').strip()
    genre      = request.form.get('genre', '').strip()

    allowed_audio = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac'}
    ext = audio_file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed_audio:
        return jsonify({'error': f'Unsupported format. Allowed: {", ".join(allowed_audio)}'}), 400

    s3 = get_s3()
    audio_key = f"songs/{request.user_id}/{uuid.uuid4()}.{ext}"

    try:
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)

        s3.upload_fileobj(
            audio_file,
            S3_BUCKET,
            audio_key,
            ExtraArgs={'ContentType': f'audio/{ext}'}
        )
    except NoCredentialsError:
        return jsonify({'error': 'AWS credentials error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Handle optional cover image
    cover_key = None
    if 'cover' in request.files:
        cover_file = request.files['cover']
        cover_ext  = cover_file.filename.rsplit('.', 1)[-1].lower()
        if cover_ext in {'jpg', 'jpeg', 'png', 'webp'}:
            cover_key = f"covers/{request.user_id}/{uuid.uuid4()}.{cover_ext}"
            s3.upload_fileobj(cover_file, S3_BUCKET, cover_key,
                              ExtraArgs={'ContentType': f'image/{cover_ext}'})

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO songs (user_id, title, artist, album, genre, s3_key, cover_s3_key, file_size)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (request.user_id, title, artist, album, genre, audio_key, cover_key, file_size))
            song_id = c.lastrowid
        return jsonify({'message': 'Song uploaded!', 'song_id': song_id}), 201
    finally:
        conn.close()


@app.route('/api/songs', methods=['GET'])
@token_required
def get_songs():
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT s.id, s.title, s.artist, s.album, s.genre,
                       s.s3_key, s.cover_s3_key, s.duration, s.file_size,
                       s.uploaded_at, u.name as uploader_name
                FROM songs s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.uploaded_at DESC
            """)
            songs = c.fetchall()

        s3 = get_s3()
        for song in songs:
            song['audio_url'] = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': song['s3_key']},
                ExpiresIn=3600
            )
            if song['cover_s3_key']:
                song['cover_url'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': song['cover_s3_key']},
                    ExpiresIn=3600
                )
            else:
                song['cover_url'] = None
            # Convert datetime to string
            if song['uploaded_at']:
                song['uploaded_at'] = song['uploaded_at'].isoformat()

        return jsonify({'songs': songs}), 200
    finally:
        conn.close()


@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
@token_required
def delete_song(song_id):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("SELECT s3_key, cover_s3_key, user_id FROM songs WHERE id=%s", (song_id,))
            song = c.fetchone()
            if not song:
                return jsonify({'error': 'Song not found'}), 404
            if song['user_id'] != request.user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            s3 = get_s3()
            s3.delete_object(Bucket=S3_BUCKET, Key=song['s3_key'])
            if song['cover_s3_key']:
                s3.delete_object(Bucket=S3_BUCKET, Key=song['cover_s3_key'])

            c.execute("DELETE FROM songs WHERE id=%s", (song_id,))
        return jsonify({'message': 'Song deleted'}), 200
    finally:
        conn.close()


@app.route('/api/songs/my', methods=['GET'])
@token_required
def my_songs():
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, title, artist, album, genre, s3_key, cover_s3_key,
                       duration, file_size, uploaded_at
                FROM songs WHERE user_id=%s ORDER BY uploaded_at DESC
            """, (request.user_id,))
            songs = c.fetchall()

        s3 = get_s3()
        for song in songs:
            song['audio_url'] = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': song['s3_key']},
                ExpiresIn=3600
            )
            if song['cover_s3_key']:
                song['cover_url'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': song['cover_s3_key']},
                    ExpiresIn=3600
                )
            else:
                song['cover_url'] = None
            if song['uploaded_at']:
                song['uploaded_at'] = song['uploaded_at'].isoformat()

        return jsonify({'songs': songs}), 200
    finally:
        conn.close()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)