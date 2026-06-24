"""
أوامر المطور النصية - تعمل بصيغة "أمر [ID]" أو "أمر [نص]"
كلها محمية بفحص is_developer
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.permissions import is_developer
from database import users as db_users

logger = logging.getLogger(__name__)


def _extract_group_id(args: list[str]) -> int | None:
    if not args:
        return None
    try:
        return int(args[0])
    except ValueError:
        return None


async def cmd_ban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args)
    if group_id is None:
        await message.reply_text("استخدم: حظر مجموعة [ID]")
        return
    await db_users.set_group_ban(group_id, True)
    await message.reply_text(f"🚫 تم حظر المجموعة {group_id}")


async def cmd_unban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args)
    if group_id is None:
        await message.reply_text("استخدم: فك حظر مجموعة [ID]")
        return
    await db_users.set_group_ban(group_id, False)
    await message.reply_text(f"✅ تم فك حظر المجموعة {group_id}")


async def cmd_activate_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args)
    if group_id is None:
        await message.reply_text("استخدم: تفعيل مجموعة [ID]")
        return
    await db_users.set_group_active(group_id, True)
    await message.reply_text(f"✅ تم تفعيل المجموعة {group_id}")


async def cmd_deactivate_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args)
    if group_id is None:
        await message.reply_text("استخدم: تعطيل مجموعة [ID]")
        return
    await db_users.set_group_active(group_id, False)
    await message.reply_text(f"⏸ تم تعطيل المجموعة {group_id}")


async def cmd_toggle_ai_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args) or update.effective_chat.id
    await db_users.set_group_ai_enabled(group_id, True)
    await message.reply_text(f"🤖 تم تشغيل الذكاء الاصطناعي بالمجموعة {group_id}")


async def cmd_toggle_ai_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return
    group_id = _extract_group_id(context.args) or update.effective_chat.id
    await db_users.set_group_ai_enabled(group_id, False)
    await message.reply_text(f"🔇 تم إيقاف الذكاء الاصطناعي بالمجموعة {group_id}")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: إذاعة [النص] - يرسل لكل المجموعات المفعّلة"""
    message = update.effective_message
    if not is_developer(update.effective_user.id):
        return

    text = " ".join(context.args)
    if not text:
        await message.reply_text("استخدم: إذاعة [النص]")
        return

    group_ids = await db_users.get_all_group_ids()
    sent, failed = 0, 0

    status_msg = await message.reply_text(f"📢 بدء الإذاعة لـ {len(group_ids)} مجموعة...")

    for group_id in group_ids:
        try:
            await context.bot.send_message(chat_id=group_id, text=f"📢 إعلان:\n\n{text}")
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning(f"فشل إرسال الإذاعة للمجموعة {group_id}: {e}")
        await asyncio.sleep(0.05)  # تجنب تجاوز حدود تيليغرام للسرعة

    await status_msg.edit_text(f"✅ تمت الإذاعة\n\nنجح: {sent}\nفشل: {failed}")
