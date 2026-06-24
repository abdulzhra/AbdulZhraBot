"""
طبقة الاتصال بقاعدة بيانات PostgreSQL
تستخدم asyncpg لإنشاء pool اتصالات يستخدمه كل البوت
"""
import asyncpg
import logging
from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)

# الـ pool العام للاتصالات - يُستخدم في كل مكان بالبوت
_pool: asyncpg.Pool | None = None


async def init_db_pool():
    """
    إنشاء pool اتصالات بقاعدة البيانات.
    يجب استدعاء هذه الدالة مرة واحدة عند بدء تشغيل البوت.
    """
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح")
    return _pool


async def close_db_pool():
    """إغلاق pool الاتصالات عند إيقاف البوت"""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("🔌 تم إغلاق الاتصال بقاعدة البيانات")


def get_pool() -> asyncpg.Pool:
    """
    إرجاع pool الاتصالات الحالي.
    يُستخدم من باقي ملفات قاعدة البيانات لتنفيذ الاستعلامات.
    """
    if _pool is None:
        raise RuntimeError(
            "⚠️ لم يتم تهيئة pool قاعدة البيانات بعد. استدعِ init_db_pool() أولاً."
        )
    return _pool
