"""
دوال التعامل مع جدول auto_replies - نظام الردود الذكية المخصصة
كل كلمة (trigger_word) يمكن أن يكون لها أكثر من رد، ويتم اختيار واحد عشوائياً
"""
import random
from database.connection import get_pool


async def add_reply(group_id: int, trigger_word: str, reply_type: str,
                     reply_content: str, created_by: int):
    """
    reply_type: text / photo / video / sticker / document
    reply_content: النص، أو file_id بالنسبة للصور/الفيديو/الملصقات/الملفات
    """
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO auto_replies (group_id, trigger_word, reply_type, reply_content, created_by)
        VALUES ($1, $2, $3, $4, $5)
        """,
        group_id, trigger_word.lower().strip(), reply_type, reply_content, created_by,
    )


async def get_random_reply(group_id: int, trigger_word: str):
    """يرجع رداً عشوائياً واحداً لكلمة معينة، أو None إن لم توجد ردود"""
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT * FROM auto_replies WHERE group_id = $1 AND trigger_word = $2",
        group_id, trigger_word.lower().strip(),
    )
    if not rows:
        return None
    return random.choice(rows)


async def get_all_triggers(group_id: int) -> list[str]:
    """يرجع كل الكلمات المفعّلة كردود ذكية في مجموعة معينة (بدون تكرار)"""
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT DISTINCT trigger_word FROM auto_replies WHERE group_id = $1",
        group_id,
    )
    return [r["trigger_word"] for r in rows]


async def delete_reply_by_id(reply_id: int, group_id: int) -> bool:
    pool = get_pool()
    result = await pool.execute(
        "DELETE FROM auto_replies WHERE id = $1 AND group_id = $2",
        reply_id, group_id,
    )
    return result != "DELETE 0"


async def delete_all_replies_for_trigger(group_id: int, trigger_word: str):
    pool = get_pool()
    await pool.execute(
        "DELETE FROM auto_replies WHERE group_id = $1 AND trigger_word = $2",
        group_id, trigger_word.lower().strip(),
    )


async def search_replies(group_id: int, keyword: str, limit: int = 20):
    pool = get_pool()
    return await pool.fetch(
        """
        SELECT * FROM auto_replies
        WHERE group_id = $1 AND trigger_word ILIKE $2
        LIMIT $3
        """,
        group_id, f"%{keyword}%", limit,
    )
