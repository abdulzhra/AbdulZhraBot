"""
نظام الاقتراحات والشكاوى
المستخدمون يرسلون، والمطور يقبل/يرفض/يتابع من الخاص
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import DEVELOPER_ID
from database.connection import get_pool
from utils.permissions import is_developer


# ============== الاقتراحات ==============

async def cmd_send_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: اقتراح [النص]"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    text = " ".join(context.args) if context.args else None
    if not text:
        await message.reply_text("استخدم: اقتراح [النص]")
        return

    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO suggestions (group_id, user_id, content)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        chat.id, user.id, text,
    )
    suggestion_id = row["id"]

    await message.reply_text("✅ تم إرسال اقتراحك للإدارة، شكراً لك 🙏")

    # إرسال نسخة للمطور بأزرار قبول/رفض
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"suggestion:accept:{suggestion_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"suggestion:reject:{suggestion_id}"),
        ]
    ])
    try:
        await context.bot.send_message(
            DEVELOPER_ID,
            f"💡 اقتراح جديد من {user.first_name} (ID: {user.id})\nبالمجموعة: {chat.title}\n\n{text}",
            reply_markup=keyboard,
        )
    except Exception:
        pass


async def suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغطات أزرار قبول/رفض الاقتراح"""
    query = update.callback_query
    if not is_developer(update.effective_user.id):
        await query.answer("هذا للمطور فقط 🚫", show_alert=True)
        return

    await query.answer()
    _, action, suggestion_id = query.data.split(":")
    suggestion_id = int(suggestion_id)

    pool = get_pool()
    new_status = "accepted" if action == "accept" else "rejected"
    await pool.execute(
        "UPDATE suggestions SET status = $1 WHERE id = $2", new_status, suggestion_id
    )

    label = "✅ تم قبول هذا الاقتراح" if action == "accept" else "❌ تم رفض هذا الاقتراح"
    await query.edit_message_text(f"{query.message.text}\n\n{label}")


# ============== الشكاوى ==============

async def cmd_send_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: شكوى [النص]"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    text = " ".join(context.args) if context.args else None
    if not text:
        await message.reply_text("استخدم: شكوى [النص]")
        return

    pool = get_pool()
    await pool.execute(
        "INSERT INTO complaints (group_id, user_id, content) VALUES ($1, $2, $3)",
        chat.id, user.id, text,
    )

    await message.reply_text("✅ تم تحويل شكواك للإدارة 🙏")

    try:
        await context.bot.send_message(
            DEVELOPER_ID,
            f"⚠️ شكوى جديدة من {user.first_name} (ID: {user.id})\nبالمجموعة: {chat.title}\n\n{text}",
        )
    except Exception:
        pass
