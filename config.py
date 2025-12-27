import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'scan2eat-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/scan2eat'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QR_CODE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'qr_codes')
