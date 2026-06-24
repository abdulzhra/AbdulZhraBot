"""
إنشاء جميع جداول قاعدة البيانات الأساسية للبوت.
يتم استدعاء create_all_tables() مرة واحدة عند بدء تشغيل البوت،
وهي تستخدم CREATE TABLE IF NOT EXISTS فلا تكرر العملية إذا كانت الجداول موجودة.
"""
import logging
from database.connection import get_pool

logger = logging.getLogger(__name__)


SCHEMA_STATEMENTS = [
    # ---------- جدول المستخدمين ----------
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        is_banned BOOLEAN DEFAULT FALSE,
        joined_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # ---------- جدول المجموعات ----------
    """
    CREATE TABLE IF NOT EXISTS groups (
        group_id BIGINT PRIMARY KEY,
        title TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        is_banned BOOLEAN DEFAULT FALSE,
        ai_enabled BOOLEAN DEFAULT TRUE,
        games_enabled BOOLEAN DEFAULT TRUE,
        added_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # ---------- جدول أعضاء المجموعات (نقاط، خبرة، رتب) ----------
    """
    CREATE TABLE IF NOT EXISTS group_members (
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        rank TEXT DEFAULT 'عضو',
        points INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        message_count INTEGER DEFAULT 0,
        wins_count INTEGER DEFAULT 0,
        warnings INTEGER DEFAULT 0,
        last_message_at TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (group_id, user_id)
    );
    """,

    # ---------- جدول محفظة الاقتصاد ----------
    """
    CREATE TABLE IF NOT EXISTS wallets (
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        balance BIGINT DEFAULT 0,
        bank_balance BIGINT DEFAULT 0,
        title TEXT DEFAULT 'فقير',
        job TEXT,
        last_salary_at TIMESTAMP,
        last_daily_at TIMESTAMP,
        PRIMARY KEY (group_id, user_id)
    );
    """,

    # ---------- جدول الردود الذكية (الكلمة + الردود المتعددة) ----------
    """
    CREATE TABLE IF NOT EXISTS auto_replies (
        id SERIAL PRIMARY KEY,
        group_id BIGINT NOT NULL,
        trigger_word TEXT NOT NULL,
        reply_type TEXT NOT NULL DEFAULT 'text',
        reply_content TEXT NOT NULL,
        is_pinned BOOLEAN DEFAULT FALSE,
        created_by BIGINT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_auto_replies_group_trigger
    ON auto_replies (group_id, trigger_word);
    """,

    # ---------- جدول سياق محادثة الذكاء الاصطناعي ----------
    """
    CREATE TABLE IF NOT EXISTS ai_conversation_history (
        id SERIAL PRIMARY KEY,
        group_id BIGINT NOT NULL,
        user_id BIGINT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_ai_history_group
    ON ai_conversation_history (group_id, created_at);
    """,

    # ---------- جدول التحذيرات ----------
    """
    CREATE TABLE IF NOT EXISTS warnings_log (
        id SERIAL PRIMARY KEY,
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        reason TEXT,
        issued_by BIGINT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # ---------- جدول الاقتراحات والشكاوى ----------
    """
    CREATE TABLE IF NOT EXISTS suggestions (
        id SERIAL PRIMARY KEY,
        group_id BIGINT,
        user_id BIGINT NOT NULL,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS complaints (
        id SERIAL PRIMARY KEY,
        group_id BIGINT,
        user_id BIGINT NOT NULL,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # ---------- جدول سجل الأخطاء ----------
    """
    CREATE TABLE IF NOT EXISTS error_logs (
        id SERIAL PRIMARY KEY,
        error_text TEXT NOT NULL,
        context TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
]


async def create_all_tables():
    """تنفيذ كل جمل إنشاء الجداول دفعة واحدة عبر transaction واحد"""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for statement in SCHEMA_STATEMENTS:
                await conn.execute(statement)
    logger.info("✅ تم التحقق من جميع الجداول/إنشاؤها بنجاح")
