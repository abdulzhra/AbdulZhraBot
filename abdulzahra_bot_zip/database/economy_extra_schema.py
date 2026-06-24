"""
جداول إضافية لتوسعة نظام الاقتصاد: الممتلكات (بيوت/سيارات/شركات) + الزواج الوهمي
يتم استدعاء create_economy_extra_tables() مرة واحدة عند بدء تشغيل البوت (إضافة على create_all_tables)
"""
from database.connection import get_pool

EXTRA_SCHEMA_STATEMENTS = [
    # ---------- جدول الممتلكات (بيوت/قصور/شركات/فنادق/سيارات) ----------
    """
    CREATE TABLE IF NOT EXISTS properties (
        id SERIAL PRIMARY KEY,
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        item_type TEXT NOT NULL,
        item_name TEXT NOT NULL,
        purchased_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_properties_owner
    ON properties (group_id, user_id);
    """,

    # ---------- جدول الزواج الوهمي ----------
    """
    CREATE TABLE IF NOT EXISTS marriages (
        id SERIAL PRIMARY KEY,
        group_id BIGINT NOT NULL,
        user_id_1 BIGINT NOT NULL,
        user_id_2 BIGINT NOT NULL,
        married_at TIMESTAMP DEFAULT NOW()
    );
    """,
]


async def create_economy_extra_tables():
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for statement in EXTRA_SCHEMA_STATEMENTS:
                await conn.execute(statement)
