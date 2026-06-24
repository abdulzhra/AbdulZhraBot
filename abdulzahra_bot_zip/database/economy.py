"""
دوال التعامل مع جدول wallets - نظام الاقتصاد (دينار جونير)
"""
from datetime import datetime, timedelta
from database.connection import get_pool

STARTING_BALANCE = 500
DAILY_SALARY = 250


async def ensure_wallet(group_id: int, user_id: int):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO wallets (group_id, user_id, balance)
        VALUES ($1, $2, $3)
        ON CONFLICT (group_id, user_id) DO NOTHING
        """,
        group_id, user_id, STARTING_BALANCE,
    )


async def get_wallet(group_id: int, user_id: int):
    pool = get_pool()
    await ensure_wallet(group_id, user_id)
    return await pool.fetchrow(
        "SELECT * FROM wallets WHERE group_id = $1 AND user_id = $2",
        group_id, user_id,
    )


async def add_balance(group_id: int, user_id: int, amount: int):
    """إضافة (أو خصم إذا كان amount سالباً) من رصيد المحفظة"""
    pool = get_pool()
    await ensure_wallet(group_id, user_id)
    await pool.execute(
        "UPDATE wallets SET balance = balance + $1 WHERE group_id = $2 AND user_id = $3",
        amount, group_id, user_id,
    )


async def transfer_balance(group_id: int, from_user: int, to_user: int, amount: int) -> bool:
    """
    تحويل مبلغ من مستخدم لآخر داخل نفس المجموعة.
    يرجع False إذا كان الرصيد غير كافٍ.
    """
    pool = get_pool()
    await ensure_wallet(group_id, from_user)
    await ensure_wallet(group_id, to_user)
    async with pool.acquire() as conn:
        async with conn.transaction():
            sender = await conn.fetchrow(
                "SELECT balance FROM wallets WHERE group_id = $1 AND user_id = $2 FOR UPDATE",
                group_id, from_user,
            )
            if sender is None or sender["balance"] < amount:
                return False
            await conn.execute(
                "UPDATE wallets SET balance = balance - $1 WHERE group_id = $2 AND user_id = $3",
                amount, group_id, from_user,
            )
            await conn.execute(
                "UPDATE wallets SET balance = balance + $1 WHERE group_id = $2 AND user_id = $3",
                amount, group_id, to_user,
            )
    return True


async def deposit_to_bank(group_id: int, user_id: int, amount: int) -> bool:
    pool = get_pool()
    wallet = await get_wallet(group_id, user_id)
    if wallet["balance"] < amount:
        return False
    await pool.execute(
        """
        UPDATE wallets
        SET balance = balance - $1, bank_balance = bank_balance + $1
        WHERE group_id = $2 AND user_id = $3
        """,
        amount, group_id, user_id,
    )
    return True


async def withdraw_from_bank(group_id: int, user_id: int, amount: int) -> bool:
    pool = get_pool()
    wallet = await get_wallet(group_id, user_id)
    if wallet["bank_balance"] < amount:
        return False
    await pool.execute(
        """
        UPDATE wallets
        SET balance = balance + $1, bank_balance = bank_balance - $1
        WHERE group_id = $2 AND user_id = $3
        """,
        amount, group_id, user_id,
    )
    return True


async def claim_daily_salary(group_id: int, user_id: int) -> tuple[bool, int]:
    """
    يعطي الراتب اليومي إذا لم يكن قد استلمه اليوم.
    يرجع (نجح, المبلغ المتبقي بالثواني/ساعات إذا فشل كرقم تقريبي للوقت المتبقي بالساعات)
    """
    pool = get_pool()
    wallet = await get_wallet(group_id, user_id)
    now = datetime.utcnow()
    last = wallet["last_daily_at"]
    if last and (now - last) < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last)
        return False, int(remaining.total_seconds() // 3600)

    await pool.execute(
        """
        UPDATE wallets
        SET balance = balance + $1, last_daily_at = NOW()
        WHERE group_id = $2 AND user_id = $3
        """,
        DAILY_SALARY, group_id, user_id,
    )
    return True, DAILY_SALARY


async def set_title(group_id: int, user_id: int, title: str):
    pool = get_pool()
    await ensure_wallet(group_id, user_id)
    await pool.execute(
        "UPDATE wallets SET title = $1 WHERE group_id = $2 AND user_id = $3",
        title, group_id, user_id,
    )


async def set_job(group_id: int, user_id: int, job: str):
    pool = get_pool()
    await ensure_wallet(group_id, user_id)
    await pool.execute(
        "UPDATE wallets SET job = $1 WHERE group_id = $2 AND user_id = $3",
        job, group_id, user_id,
    )


async def get_richest(group_id: int, limit: int = 10):
    pool = get_pool()
    return await pool.fetch(
        """
        SELECT user_id, (balance + bank_balance) AS total
        FROM wallets
        WHERE group_id = $1
        ORDER BY total DESC
        LIMIT $2
        """,
        group_id, limit,
    )
