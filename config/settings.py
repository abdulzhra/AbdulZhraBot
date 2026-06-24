"""
ملف الإعدادات المركزي للبوت
يقرأ كل المتغيرات من ملف .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# توكن بوت تيليغرام
BOT_TOKEN = os.getenv("BOT_TOKEN")

# رابط قاعدة بيانات PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# مفتاح Anthropic للذكاء الاصطناعي
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ID المطور (المنشئ الأساسي للبوت)
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

# اسم شخصية البوت
BOT_PERSONA_NAME = "جونير"

# الكلمة التي تفعّل الذكاء الاصطناعي
AI_TRIGGER_WORD = "جونير"

# نموذج الذكاء الاصطناعي المستخدم
AI_MODEL = "claude-sonnet-4-6"

# عدد الرسائل المحفوظة في سياق المحادثة لكل مجموعة
AI_CONTEXT_HISTORY_LIMIT = 10

# التحقق من وجود المتغيرات الأساسية عند تشغيل البوت
def validate_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if DEVELOPER_ID == 0:
        missing.append("DEVELOPER_ID")
    if missing:
        raise RuntimeError(
            f"⚠️ المتغيرات التالية ناقصة في ملف .env: {', '.join(missing)}"
        )
