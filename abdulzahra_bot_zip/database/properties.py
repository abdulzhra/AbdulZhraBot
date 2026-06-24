"""
دوال التعامل مع الممتلكات (بيوت/سيارات/شركات/فنادق) والزواج الوهمي
"""
from database.connection import get_pool


# ============== الممتلكات ==============

async def add_property(group_id: int, user_id: int, item_type: str, item_name: str):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO properties (group_id, user_id, item_type, item_name)
        VALUES ($1, $2, $3, $4)
        """,
        group_id, user_id, item_type, item_name,
    )


async def get_user_properties(group_id: int, user_id: int):
    pool = get_pool()
    return await pool.fetch(
        "SELECT * FROM properties WHERE group_id = $1 AND user_id = $2 ORDER BY purchased_at",
        group_id, user_id,
    )


async def count_user_properties_by_type(group_id: int, user_id: int, item_type: str) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT COUNT(*) AS c FROM properties
        WHERE group_id = $1 AND user_id = $2 AND item_type = $3
        """,
        group_id, user_id, item_type,
    )
    return row["c"]


# ============== الزواج الوهمي ==============

async def get_marriage(group_id: int, user_id: int):
    """يرجع سجل الزواج إن وُجد (بأي ترتيب للطرفين)"""
    pool = get_pool()
    return await pool.fetchrow(
        """
        SELECT * FROM marriages
        WHERE group_id = $1 AND (user_id_1 = $2 OR user_id_2 = $2)
        """,
        group_id, user_id,
    )


async def create_marriage(group_id: int, user_id_1: int, user_id_2: int):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO marriages (group_id, user_id_1, user_id_2)
        VALUES ($1, $2, $3)
        """,
        group_id, user_id_1, user_id_2,
    )


async def delete_marriage(group_id: int, user_id: int):
    pool = get_pool()
    await pool.execute(
        """
        DELETE FROM marriages
        WHERE group_id = $1 AND (user_id_1 = $2 OR user_id_2 = $2)
        """,
        group_id, user_id,
    )


def get_partner_id(marriage_row, user_id: int) -> int:
    """من سجل زواج، يرجع ID الطرف الآخر"""
    if marriage_row["user_id_1"] == user_id:
        return marriage_row["user_id_2"]
    return marriage_row["user_id_1"]
