
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# دعم لقواعد بيانات متعددة (SQLite و PostgreSQL)
_db_path = os.path.join(BASE_DIR, "database.db").replace("\\", "/")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_db_path}")

# التأكد من استخدام PostgreSQL في بيئة الإنتاج
if os.environ.get("DATABASE_URL") and "postgresql" in os.environ.get("DATABASE_URL"):
    # إعداد لقاعدة بيانات PostgreSQL
    DATABASE_URL = os.environ.get("DATABASE_URL")
else:
    # إعداد لقاعدة بيانات SQLite (الافتراضي)
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_db_path}")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

# إنشاء المجلدات الضرورية
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# إعداد لقواعد البيانات المختلفة
if "sqlite" in DATABASE_URL:
    SQLALCHEMY_ENGINE_ARGS = {"check_same_thread": False}
else:
    SQLALCHEMY_ENGINE_ARGS = {}

# إعداد لبيئة الإنتاج
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"


ALLOWED_EXTENSIONS = {".zip", ".py", ".txt", ".json", ".yaml", ".yml", ".toml", ".requirements.txt", ".cfg", ".ini", ".md", ".env", ".log", ".sh", ".bat", ".csv", ".html", ".css", ".js"}

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@admin.com")

MAX_PROJECTS_PER_USER = 10
MAX_FILE_SIZE = 50 * 1024 * 1024
