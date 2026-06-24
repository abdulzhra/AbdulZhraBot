"""
دوال التعامل مع جداول users و groups و group_members
كل دالة هنا تأخذ اتصالاً من pool وتنفذ استعلاماً واحداً محدداً
"""
from database.connection import get_pool


# ============== المستخدمون ==============

async def upsert_user(user_id: int, username: str | None, first_name: str | None):
    """تسجيل مستخدم جديد أو تحديث بياناته إذا كان موجوداً"""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO users (user_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id)
        DO UPDATE SET username = $2, first_name = $3
        """,
        user_id, username, first_name,
    )


async def is_user_banned(user_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchrow("SELECT is_banned FROM users WHERE user_id = $1", user_id)
    return bool(row and row["is_banned"])


async def set_user_ban(user_id: int, banned: bool):
    pool = get_pool()
    await pool.execute("UPDATE users SET is_banned = $1 WHERE user_id = $2", banned, user_id)


async def count_users() -> int:
    pool = get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) AS c FROM users")
    return row["c"]


# ============== المجموعات ==============

async def upsert_group(group_id: int, title: str | None):
    """تسجيل مجموعة جديدة أو تحديث اسمها"""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO groups (group_id, title)
        VALUES ($1, $2)
        ON CONFLICT (group_id)
        DO UPDATE SET title = $2
        """,
        group_id, title,
    )


async def get_group(group_id: int):
    pool = get_pool()
    return await pool.fetchrow("SELECT * FROM groups WHERE group_id = $1", group_id)


async def is_group_active(group_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT is_active, is_banned FROM groups WHERE group_id = $1", group_id
    )
    if not row:
        return True  # مجموعة جديدة لم تُسجل بعد تعتبر مفعّلة افتراضياً
    return row["is_active"] and not row["is_banned"]


async def set_group_active(group_id: int, active: bool):
    pool = get_pool()
    await pool.execute("UPDATE groups SET is_active = $1 WHERE group_id = $2", active, group_id)


async def set_group_ban(group_id: int, banned: bool):
    pool = get_pool()
    await pool.execute("UPDATE groups SET is_banned = $1 WHERE group_id = $2", banned, group_id)


async def set_group_ai_enabled(group_id: int, enabled: bool):
    pool = get_pool()
    await pool.execute(
        "UPDATE groups SET ai_enabled = $1 WHERE group_id = $2", enabled, group_id
    )


async def is_ai_enabled(group_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchrow("SELECT ai_enabled FROM groups WHERE group_id = $1", group_id)
    return bool(row is None or row["ai_enabled"])


async def count_groups() -> int:
    pool = get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) AS c FROM groups")
    return row["c"]


async def count_active_groups() -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT COUNT(*) AS c FROM groups WHERE is_active = TRUE AND is_banned = FALSE"
    )
    return row["c"]


async def get_all_group_ids() -> list[int]:
    pool = get_pool()
    rows = await pool.fetch("SELECT group_id FROM groups WHERE is_banned = FALSE")
    return [r["group_id"] for r in rows]


# ============== أعضاء المجموعات (نقاط/خبرة/رتب) ==============

async def ensure_member(group_id: int, user_id: int):
    """التأكد من وجود سجل للعضو في المجموعة، وإنشاؤه إذا لم يكن موجوداً"""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO group_members (group_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT (group_id, user_id) DO NOTHING
        """,
        group_id, user_id,
    )


async def increment_member_activity(group_id: int, user_id: int, points: int = 1, xp: int = 2):
    """يُستدعى عند كل رسالة لتحديث عدد الرسائل والنقاط والخبرة"""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO group_members (group_id, user_id, points, xp, message_count, last_message_at)
        VALUES ($1, $2, $3, $4, 1, NOW())
        ON CONFLICT (group_id, user_id)
        DO UPDATE SET
            points = group_members.points + $3,
            xp = group_members.xp + $4,
            message_count = group_members.message_count + 1,
            last_message_at = NOW()
        """,
        group_id, user_id, points, xp,
    )


async def get_member(group_id: int, user_id: int):
    pool = get_pool()
    return await pool.fetchrow(
        "SELECT * FROM group_members WHERE group_id = $1 AND user_id = $2",
        group_id, user_id,
    )


async def get_member_rank(group_id: int, user_id: int) -> str:
    pool = get_pool()
    await ensure_member(group_id, user_id)
    row = await pool.fetchrow(
        "SELECT rank FROM group_members WHERE group_id = $1 AND user_id = $2",
        group_id, user_id,
    )
    return row["rank"] if row else "عضو"


async def set_member_rank(group_id: int, user_id: int, rank: str):
    pool = get_pool()
    await ensure_member(group_id, user_id)
    await pool.execute(
        "UPDATE group_members SET rank = $1 WHERE group_id = $2 AND user_id = $3",
        rank, group_id, user_id,
    )


async def get_top_members(group_id: int, by: str = "points", limit: int = 10):
    """
    by: points / xp / message_count / wins_count
    """
    allowed = {"points", "xp", "message_count", "wins_count"}
    column = by if by in allowed else "points"
    pool = get_pool()
    return await pool.fetch(
        f"""
        SELECT user_id, {column} AS value
        FROM group_members
        WHERE group_id = $1
        ORDER BY {column} DESC
        LIMIT $2
        """,
        group_id, limit,
    )
