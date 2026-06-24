"""
لوحة تحكم المطور - تعمل بالكامل داخل تيليغرام بأزرار Inline
الوصول مقيّد فقط لـ DEVELOPER_ID
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.permissions import is_developer
from database import users as db_users


def _main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="dev:stats")],
        [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="dev:groups")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="dev:settings")],
        [InlineKeyboardButton("📢 الإذاعة", callback_data="dev:broadcast")],
    ]
    return InlineKeyboardMarkup(buttons)


async def cmd_dev_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر فتح لوحة المطور - يعمل فقط بالخاص ومع المطور"""
    user = update.effective_user
    message = update.effective_message

    if not is_developer(user.id):
        await message.reply_text("هذا الأمر للمطور فقط 🚫")
        return

    await message.reply_text(
        "🛠 لوحة تحكم المطور\n\nاختر القسم اللي تريده:",
        reply_markup=_main_menu_keyboard(),
    )


async def dev_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج كل ضغطات أزرار لوحة المطور"""
    query = update.callback_query
    user = update.effective_user

    if not is_developer(user.id):
        await query.answer("هذا القسم للمطور فقط 🚫", show_alert=True)
        return

    await query.answer()
    action = query.data

    if action == "dev:stats":
        await _show_stats(query)
    elif action == "dev:groups":
        await _show_groups_menu(query)
    elif action == "dev:settings":
        await _show_settings_menu(query)
    elif action == "dev:broadcast":
        await query.edit_message_text(
            "📢 لإرسال إذاعة، استخدم الأمر:\n\n"
            "إذاعة [النص]\n\n"
            "وسيتم إرسالها لكل المجموعات المفعّلة.",
            reply_markup=_back_keyboard(),
        )
    elif action == "dev:back":
        await query.edit_message_text(
            "🛠 لوحة تحكم المطور\n\nاختر القسم اللي تريده:",
            reply_markup=_main_menu_keyboard(),
        )


def _back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="dev:back")]])


async def _show_stats(query):
    total_users = await db_users.count_users()
    total_groups = await db_users.count_groups()
    active_groups = await db_users.count_active_groups()

    text = (
        "📊 إحصائيات البوت\n\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"📂 عدد المجموعات: {total_groups}\n"
        f"✅ المجموعات المفعّلة: {active_groups}"
    )
    await query.edit_message_text(text, reply_markup=_back_keyboard())


async def _show_groups_menu(query):
    text = (
        "👥 إدارة المجموعات\n\n"
        "استخدم الأوامر التالية بالرد على رسالة من المجموعة أو بكتابة الـ ID:\n\n"
        "حظر مجموعة [ID]\n"
        "فك حظر مجموعة [ID]\n"
        "تفعيل مجموعة [ID]\n"
        "تعطيل مجموعة [ID]"
    )
    await query.edit_message_text(text, reply_markup=_back_keyboard())


async def _show_settings_menu(query):
    text = (
        "⚙️ الإعدادات العامة\n\n"
        "تشغيل الذكاء الاصطناعي [ID المجموعة]\n"
        "ايقاف الذكاء الاصطناعي [ID المجموعة]"
    )
    await query.edit_message_text(text, reply_markup=_back_keyboard())
