"""
نظام الترحيب التلقائي بالأعضاء الجدد + رسالة المغادرة
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 قوانين الكروب", callback_data="welcome:rules")]
        ])
        text = (
            f"👋 هلا وسهلا {new_member.first_name} بكروب {chat.title}!\n"
            f"خوش وحدة زادت 😄"
        )
        await message.reply_text(text, reply_markup=keyboard)


async def member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    left_member = message.left_chat_member

    if left_member and not left_member.is_bot:
        await message.reply_text(f"😢 {left_member.first_name} طلع من الكروب... باي باي")


async def welcome_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📜 قوانين الكروب:\n\n"
        "1- الاحترام المتبادل.\n"
        "2- ممنوع السبام والإعلانات.\n"
        "3- ممنوع الروابط بدون إذن الإدارة.\n"
        "4- احترام الأدمنية والمشرفين."
    )
