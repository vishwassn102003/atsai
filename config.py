import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY                     = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL', 'sqlite:///atsai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # gemini
    GEMINI_API_KEY  = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL    = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')

    # Google OAuth
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # Razorpay
    RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # Pricing & subscription
    PRICE_PAISE = int(float(os.environ.get('PRICE_PAISE', 2900))) # ₹29
    SUBSCRIPTION_DAYS     = 30
    SUBSCRIPTION_EDITS    = 25

    # Upload
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
