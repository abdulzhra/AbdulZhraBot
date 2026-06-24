"""
المعالج الرئيسي لرسائل النصوص في المجموعات.
يُنفَّذ على كل رسالة نصية ترد للبوت، وبالترتيب:
1. تسجيل المستخدم والمجموعة في قاعدة البيانات.
2. تحديث نقاط النشاط/الخبرة/عدد الرسائل.
3. التحقق إن كانت الرسالة تبدأ بكلمة تفعيل "جونير" -> الذكاء الاصطناعي.
4. التحقق من الردود الذكية المخصصة المطابقة لأي كلمة في الرسالة.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import AI_TRIGGER_WORD
from database import users as db_users
from database import auto_replies as db_replies
from utils.ai_engine import get_junior_reply
from handlers.protection import check_links_protection

logger = logging.getLogger(__name__)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if message is None or chat is None or user is None:
        return
    if chat.type not in ("group", "supergroup"):
        return
    if not message.text:
        return

    text = message.text.strip()

    # 1. تسجيل المستخدم والمجموعة
    await db_users.upsert_user(user.id, user.username, user.first_name)
    await db_users.upsert_group(chat.id, chat.title)

    # التحقق من حظر المجموعة أو المستخدم
    if await db_users.is_user_banned(user.id):
        return
    if not await db_users.is_group_active(chat.id):
        return

    # فحص الحماية من الروابط (يحذف الرسالة ويصدر تحذيراً إذا وجد رابط)
    if await check_links_protection(update, context):
        return

    # فحص إن كانت الرسالة محاولة إجابة بأي لعبة جارية (تخمين رقم، ترتيب حروف، صح/خطأ...)
    from handlers.games import handle_any_game_attempt
    if await handle_any_game_attempt(update, context):
        return

    # 2. تحديث نقاط النشاط
    await db_users.increment_member_activity(chat.id, user.id)

    # 3. تفعيل جونير (الذكاء الاصطناعي)
    if text.startswith(AI_TRIGGER_WORD):
        if not await db_users.is_ai_enabled(chat.id):
            return
        question = text[len(AI_TRIGGER_WORD):].strip()
        if not question:
            return
        await context.bot.send_chat_action(chat_id=chat.id, action="typing")
        reply = await get_junior_reply(
            group_id=chat.id,
            user_id=user.id,
            user_name=user.first_name or "صاحبي",
            question=question,
        )
        await message.reply_text(reply)
        return

    # 4. الردود الذكية المخصصة - نتحقق من كل كلمة في الرسالة
    words = text.split()
    for word in words:
        reply_row = await db_replies.get_random_reply(chat.id, word)
        if reply_row:
            await _send_auto_reply(message, reply_row)
            return  # أول تطابق فقط لتجنب تكرار الردود


async def _send_auto_reply(message, reply_row):
    """يرسل الرد المخصص حسب نوعه (نص، صورة، فيديو، ملصق، ملف)"""
    reply_type = reply_row["reply_type"]
    content = reply_row["reply_content"]

    if reply_type == "text":
        await message.reply_text(content)
    elif reply_type == "photo":
        await message.reply_photo(content)
    elif reply_type == "video":
        await message.reply_video(content)
    elif reply_type == "sticker":
        await message.reply_sticker(content)
    elif reply_type == "document":
        await message.reply_document(content)
    else:
        await message.reply_text(content)
