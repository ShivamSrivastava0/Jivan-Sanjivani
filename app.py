from flask import Flask, request, jsonify
import smtplib
import random
import sqlite3
import os
import pytz
import hashlib
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_cors import CORS

# Load environment variables
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Define Timezone
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Database Setup
def get_db_connection():
    return sqlite3.connect("otp_database.db", check_same_thread=False)

def setup_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Hash OTP for security
def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

# Store OTP securely
def store_otp(email, otp):
    hashed_otp = hash_otp(otp)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO otp_storage (email, otp) VALUES (?, ?)", (email, hashed_otp))
        conn.commit()

# Send OTP via Email
def send_otp(email):
    otp = generate_otp()
    
    subject = "Your OTP Code"
    body = f"Your OTP is: {otp}\nIt expires in 5 minutes."

    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, email, message)
        store_otp(email, otp)
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False

# Verify OTP
def verify_otp(email, user_otp):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp, timestamp FROM otp_storage WHERE email=? ORDER BY timestamp DESC LIMIT 1", (email,))
        record = cursor.fetchone()

    if record:
        stored_otp, timestamp_str = record
        timestamp_utc = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        timestamp_utc = pytz.utc.localize(timestamp_utc)

        timestamp_local = timestamp_utc.astimezone(LOCAL_TIMEZONE)
        expiry_time = timestamp_local + timedelta(minutes=5)
        current_time_local = datetime.now().astimezone(LOCAL_TIMEZONE)

        if current_time_local > expiry_time:
            return "expired"

        if stored_otp != hash_otp(user_otp):
            return "invalid"

        return "success"
    return "not_found"

# Flask Routes

@app.route("/send_otp", methods=["POST"])
def send_otp_route():
    data = request.json
    email = data.get("email")

    if send_otp(email):
        return jsonify({"message": "OTP sent successfully"}), 200
    return jsonify({"error": "Failed to send OTP"}), 500

@app.route("/verify_otp", methods=["POST"])
def verify_otp_route():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    result = verify_otp(email, otp)

    if result == "success":
        return jsonify({"message": "OTP verified successfully"}), 200
    elif result == "expired":
        return jsonify({"error": "OTP expired"}), 400
    elif result == "invalid":
        return jsonify({"error": "Invalid OTP"}), 400
    return jsonify({"error": "No OTP found"}), 404


# Start the Flask app
if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
