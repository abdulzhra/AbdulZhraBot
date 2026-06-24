"""
أوامر المعلومات الأساسية: ايدي / مالك / مطور / الشهرة / توب
"""
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import DEVELOPER_ID
from database import users as db_users


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: ايدي  /  ايدي بالرد (يعرض معلومات الشخص المردود عليه)"""
    chat = update.effective_chat
    message = update.effective_message

    target_user = message.reply_to_message.from_user if message.reply_to_message else update.effective_user

    member = await db_users.get_member(chat.id, target_user.id)
    rank = member["rank"] if member else "عضو"
    msg_count = member["message_count"] if member else 0

    text = (
        f"🆔 ID: {target_user.id}\n"
        f"👤 الاسم: {target_user.full_name}\n"
        f"🔗 المعرف: @{target_user.username if target_user.username else 'لا يوجد'}\n"
        f"💬 عدد الرسائل: {msg_count}\n"
        f"🎖 الرتبة: {rank}"
    )
    await message.reply_text(text)


async def cmd_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: مالك - يعرض معلومات مالك المجموعة (المنشئ الأساسي حالياً كمرجع افتراضي)"""
    message = update.effective_message
    try:
        owner_chat = await context.bot.get_chat(DEVELOPER_ID)
        text = (
            f"👑 المالك: {owner_chat.full_name}\n"
            f"🔗 المعرف: @{owner_chat.username if owner_chat.username else 'لا يوجد'}\n"
            f"🆔 ID: {DEVELOPER_ID}"
        )
    except Exception:
        text = "تعذر جلب معلومات المالك حالياً."
    await message.reply_text(text)


async def cmd_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: مطور - يعرض معلومات المطور وإحصائيات البوت العامة"""
    message = update.effective_message
    total_users = await db_users.count_users()
    total_groups = await db_users.count_groups()
    try:
        dev_chat = await context.bot.get_chat(DEVELOPER_ID)
        dev_name = dev_chat.full_name
        dev_username = dev_chat.username or "لا يوجد"
    except Exception:
        dev_name = "غير معروف"
        dev_username = "لا يوجد"

    text = (
        f"👨‍💻 المطور: {dev_name}\n"
        f"🔗 المعرف: @{dev_username}\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"📂 عدد المجموعات: {total_groups}"
    )
    await message.reply_text(text)


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: توب - يعرض أفضل 10 أعضاء بالنقاط"""
    chat = update.effective_chat
    message = update.effective_message

    top_members = await db_users.get_top_members(chat.id, by="points", limit=10)
    if not top_members:
        await message.reply_text("لا يوجد بيانات كافية بعد بهذا الكروب.")
        return

    lines = ["🏆 توب 10 بالكروب:\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(top_members):
        try:
            user = await context.bot.get_chat(row["user_id"])
            name = user.full_name
        except Exception:
            name = f"مستخدم {row['user_id']}"
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {row['value']} نقطة")

    await message.reply_text("\n".join(lines))


async def cmd_fame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: الشهرة - يعرض أكثر عضو نشاطاً/رسائل/نقاط/فوزاً"""
    chat = update.effective_chat
    message = update.effective_message

    categories = [
        ("message_count", "💬 أكثر عضو رسائل"),
        ("points", "⭐ أكثر عضو نقاط"),
        ("wins_count", "🎮 أكثر عضو فوزاً بالألعاب"),
    ]

    lines = ["🌟 شهرة الكروب:\n"]
    for column, label in categories:
        top = await db_users.get_top_members(chat.id, by=column, limit=1)
        if top:
            try:
                user = await context.bot.get_chat(top[0]["user_id"])
                name = user.full_name
            except Exception:
                name = f"مستخدم {top[0]['user_id']}"
            lines.append(f"{label}: {name} ({top[0]['value']})")
        else:
            lines.append(f"{label}: لا يوجد بيانات بعد")

    await message.reply_text("\n".join(lines))
