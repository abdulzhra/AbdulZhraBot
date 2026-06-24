"""
نظام الرتب: رفع/تنزيل مدير، أدمن، مميز + رتب مخصصة
يستخدم منطق الصلاحيات بـ utils/permissions.py لمنع أي عضو من ترقية شخص لرتبة أعلى من رتبته
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import users as db_users
from utils.permissions import can_promote, is_developer, RANK_HIERARCHY

# تحويل من كلمة الأمر إلى اسم الرتبة الرسمي
RANK_COMMAND_MAP = {
    "مدير": "المدير",
    "أدمن": "الأدمن",
    "ادمن": "الأدمن",
    "مميز": "المميز",
    "مشرف": "المشرف",
}

DEFAULT_RANK = "عضو"


async def _get_actor_rank(chat_id: int, user_id: int) -> str:
    """رتبة الشخص الذي يصدر الأمر؛ المطور دائماً 'المنشئ الأساسي'"""
    if is_developer(user_id):
        return "المنشئ الأساسي"
    return await db_users.get_member_rank(chat_id, user_id)


async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: رفع [مدير/أدمن/مميز/مشرف] - يجب أن يكون بالرد على شخص"""
    message = update.effective_message
    chat = update.effective_chat
    actor = update.effective_user

    if not message.reply_to_message:
        await message.reply_text("لازم ترد على الشخص اللي تريد ترفعه.")
        return

    if not context.args:
        await message.reply_text("استخدم: رفع [مدير/أدمن/مميز/مشرف] (بالرد على شخص)")
        return

    rank_word = context.args[0]
    new_rank = RANK_COMMAND_MAP.get(rank_word)
    if not new_rank:
        await message.reply_text("الرتبة غير معروفة. استخدم: مدير / أدمن / مميز / مشرف")
        return

    target = message.reply_to_message.from_user
    actor_rank = await _get_actor_rank(chat.id, actor.id)
    target_current_rank = await db_users.get_member_rank(chat.id, target.id)

    if not can_promote(actor_rank, target_current_rank, new_rank):
        await message.reply_text("ما تملك صلاحية تعطي هذي الرتبة 🚫")
        return

    await db_users.set_member_rank(chat.id, target.id, new_rank)
    await message.reply_text(f"✅ تم ترفيع {target.first_name} إلى رتبة {new_rank}")


async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: تنزيل [مدير/أدمن/مميز/مشرف] - يرجع العضو لرتبة 'عضو'"""
    message = update.effective_message
    chat = update.effective_chat
    actor = update.effective_user

    if not message.reply_to_message:
        await message.reply_text("لازم ترد على الشخص اللي تريد تنزله.")
        return

    target = message.reply_to_message.from_user
    actor_rank = await _get_actor_rank(chat.id, actor.id)
    target_current_rank = await db_users.get_member_rank(chat.id, target.id)

    # التنزيل لرتبة "عضو" يحتاج فقط أن تكون رتبتك أعلى من رتبة الهدف الحالية
    if not can_promote(actor_rank, target_current_rank, DEFAULT_RANK):
        await message.reply_text("ما تملك صلاحية تنزل هذا الشخص 🚫")
        return

    await db_users.set_member_rank(chat.id, target.id, DEFAULT_RANK)
    await message.reply_text(f"⬇️ تم تنزيل {target.first_name} إلى رتبة عضو")


async def cmd_set_custom_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    أمر: رتبة مخصصة [الاسم] - بالرد على شخص
    متاح فقط للمطور/المالك لإعطاء تسمية مخصصة (تُعرض فقط، لا تغيّر مستوى الصلاحيات الهرمي)
    """
    message = update.effective_message
    chat = update.effective_chat
    actor = update.effective_user

    actor_rank = await _get_actor_rank(chat.id, actor.id)
    if actor_rank not in ("المنشئ الأساسي", "المالك"):
        await message.reply_text("هذا الأمر للمالك أو المطور فقط 🚫")
        return

    if not message.reply_to_message or not context.args:
        await message.reply_text("استخدم: رتبة مخصصة [الاسم] (بالرد على شخص)")
        return

    custom_name = " ".join(context.args)
    target = message.reply_to_message.from_user
    await db_users.set_member_rank(chat.id, target.id, custom_name)
    await message.reply_text(f"🎖 تم إعطاء {target.first_name} رتبة مخصصة: {custom_name}")


async def cmd_show_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: الرتب - يعرض الترتيب الهرمي للرتب"""
    message = update.effective_message
    text = "🎖 ترتيب الرتب من الأعلى للأدنى:\n\n"
    text += "\n".join(f"{i + 1}. {r}" for i, r in enumerate(RANK_HIERARCHY))
    await message.reply_text(text)
