"""
نظام الحماية الأساسي: منع الروابط + نظام التحذيرات (تحذير 1، 2، 3 ثم كتم)
"""
import re
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database.connection import get_pool
from utils.permissions import is_developer

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/)", re.IGNORECASE)

MAX_WARNINGS_BEFORE_MUTE = 3


async def check_links_protection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    يتحقق من وجود روابط بالرسالة ويصدر تحذيراً عند الحاجة.
    يرجع True إذا تم اتخاذ إجراء (لإيقاف باقي المعالجة على هذه الرسالة).
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message.text or chat.type not in ("group", "supergroup"):
        return False
    if is_developer(user.id):
        return False
    if not URL_PATTERN.search(message.text):
        return False

    # تجاهل تحذير المشرفين/الأدمن (تبسيط: نتحقق من صلاحيات تيليغرام الفعلية)
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status in ("administrator", "creator"):
        return False

    try:
        await message.delete()
    except BadRequest:
        pass

    warnings_count = await _add_warning(chat.id, user.id, reason="رابط ممنوع")

    if warnings_count >= MAX_WARNINGS_BEFORE_MUTE:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=context.bot_data.get("muted_permissions"),
            )
            await context.bot.send_message(
                chat.id,
                f"🔇 {user.first_name} تم كتمه بعد 3 تحذيرات (روابط ممنوعة)."
            )
        except BadRequest as e:
            logger.warning(f"فشل كتم العضو: {e}")
    else:
        await context.bot.send_message(
            chat.id,
            f"⚠️ {user.first_name} تحذير {warnings_count}/3 — ممنوع إرسال الروابط بالكروب."
        )

    return True


async def _add_warning(group_id: int, user_id: int, reason: str) -> int:
    pool = get_pool()
    await pool.execute(
        "INSERT INTO warnings_log (group_id, user_id, reason) VALUES ($1, $2, $3)",
        group_id, user_id, reason,
    )
    await pool.execute(
        """
        UPDATE group_members SET warnings = warnings + 1
        WHERE group_id = $1 AND user_id = $2
        """,
        group_id, user_id,
    )
    row = await pool.fetchrow(
        "SELECT warnings FROM group_members WHERE group_id = $1 AND user_id = $2",
        group_id, user_id,
    )
    return row["warnings"] if row else 1
