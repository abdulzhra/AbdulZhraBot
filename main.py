"""
الملف الرئيسي لتشغيل بوت "عبد الزهرة جونير"
يقوم بـ:
1. التحقق من صحة الإعدادات.
2. الاتصال بقاعدة البيانات وإنشاء كل الجداول (الأساسية + التوسعة).
3. تسجيل كل المعالجات (Handlers) من كل الملفات.
4. بدء تشغيل البوت بنظام polling.
"""
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config.settings import BOT_TOKEN, validate_config
from database.connection import init_db_pool, close_db_pool
from database.schema import create_all_tables
from database.economy_extra_schema import create_economy_extra_tables

from handlers.messages import handle_group_message
from handlers.info_commands import cmd_id, cmd_owner, cmd_developer, cmd_top, cmd_fame
from handlers.economy_commands import (
    cmd_balance, cmd_daily_salary, cmd_deposit, cmd_withdraw,
    cmd_bank_balance, cmd_transfer,
)
from handlers.economy_extra import (
    cmd_buy_title, cmd_buy_property, cmd_buy_car, cmd_my_properties,
    cmd_marry, cmd_divorce, cmd_partner,
    cmd_get_job, cmd_work,
    cmd_luck, cmd_gamble, cmd_box, cmd_steal, cmd_invest,
)
from handlers.ranks import cmd_promote, cmd_demote, cmd_set_custom_rank, cmd_show_ranks
from handlers.games import (
    cmd_start_guess_game, cmd_rock_paper_scissors, cmd_start_unscramble,
    cmd_start_truefalse, cmd_start_math, cmd_start_memory,
    cmd_start_complete_sentence, cmd_start_quiz,
)
from handlers.suggestions import (
    cmd_send_suggestion, suggestion_callback, cmd_send_complaint,
)
from handlers.backup import cmd_backup, cmd_restore_instructions, handle_restore_file, log_error_to_db
from handlers.dev_panel import cmd_dev_panel, dev_panel_callback
from handlers.dev_commands import (
    cmd_ban_group, cmd_unban_group, cmd_activate_group, cmd_deactivate_group,
    cmd_toggle_ai_on, cmd_toggle_ai_off, cmd_broadcast,
)
from handlers.welcome import welcome_new_member, member_left, welcome_rules_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "هلا 👋 أنا جونير، بوت الكروب.\n"
        "اكتب: جونير [سؤالك] وأنا أرد عليك.\n"
        "اكتب: مساعدة لعرض كل الأوامر."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 أوامر البوت\n\n"
        "🤖 الذكاء الاصطناعي:\nجونير [سؤالك]\n\n"
        "ℹ️ المعلومات:\nايدي، ايدي بالرد، مالك، مطور، توب، الشهرة، الرتب\n\n"
        "💰 الاقتصاد:\nفلوسي، راتب، ايداع [مبلغ]، سحب [مبلغ]، رصيد البنك، تحويل [مبلغ] (بالرد)\n"
        "شراء لقب [الاسم]، شراء بيت/قصر/شركة/فندق، شراء سيارة/سيارة رياضية/سيارة فخمة\n"
        "ممتلكاتي، وظيفة [الاسم]، عمل، حظ، مقامرة [مبلغ]، صندوق، سرقة (بالرد)، استثمار [مبلغ]\n"
        "زواج (بالرد)، طلاق، شريك\n\n"
        "🎮 الألعاب:\nتخمين الرقم، حجر ورقة مقص [حجر/ورقة/مقص]، ترتيب الحروف، صح أو خطأ،\n"
        "الحساب السريع، الذاكرة، أكمل الجملة، سؤال وجواب\n\n"
        "📨 اقتراح/شكوى:\nاقتراح [النص]، شكوى [النص]\n\n"
        "🎖 الرتب:\nرفع [مدير/أدمن/مميز/مشرف] (بالرد)، تنزيل (بالرد)"
    )
    await update.effective_message.reply_text(text)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """يُسجل كل خطأ غير متوقع بقاعدة البيانات وبالـ logs"""
    logger.error("حدث خطأ غير متوقع", exc_info=context.error)
    try:
        await log_error_to_db(str(context.error), context_info=str(update))
    except Exception:
        pass


async def post_init(application: Application):
    """يُنفَّذ بعد بدء تشغيل التطبيق مباشرة - تهيئة قاعدة البيانات"""
    await init_db_pool()
    await create_all_tables()
    await create_economy_extra_tables()
    # صلاحيات الكتم الجاهزة لإعادة استخدامها بنظام الحماية
    application.bot_data["muted_permissions"] = ChatPermissions(can_send_messages=False)
    logger.info("🚀 البوت جاهز للعمل")


async def post_shutdown(application: Application):
    await close_db_pool()


def build_application() -> Application:
    validate_config()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ---------- أوامر عامة ----------
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("dev", cmd_dev_panel))
    application.add_handler(MessageHandler(filters.Regex(r"^مساعدة$"), cmd_help))

    # ---------- أوامر المعلومات ----------
    application.add_handler(MessageHandler(filters.Regex(r"^ايدي بالرد$|^ايدي$"), cmd_id))
    application.add_handler(MessageHandler(filters.Regex(r"^مالك$"), cmd_owner))
    application.add_handler(MessageHandler(filters.Regex(r"^مطور$"), cmd_developer))
    application.add_handler(MessageHandler(filters.Regex(r"^توب$"), cmd_top))
    application.add_handler(MessageHandler(filters.Regex(r"^الشهرة$"), cmd_fame))
    application.add_handler(MessageHandler(filters.Regex(r"^الرتب$"), cmd_show_ranks))

    # ---------- أوامر الاقتصاد الأساسية ----------
    application.add_handler(MessageHandler(filters.Regex(r"^(فلوسي|رصيدي|محفظتي)$"), cmd_balance))
    application.add_handler(MessageHandler(filters.Regex(r"^راتب$"), cmd_daily_salary))
    application.add_handler(MessageHandler(filters.Regex(r"^رصيد البنك$"), cmd_bank_balance))
    application.add_handler(MessageHandler(filters.Regex(r"^ايداع\s+\d+$"), cmd_deposit))
    application.add_handler(MessageHandler(filters.Regex(r"^سحب\s+\d+$"), cmd_withdraw))
    application.add_handler(MessageHandler(filters.Regex(r"^تحويل\s+\d+$"), cmd_transfer))

    # ---------- توسعة الاقتصاد: المتجر/العقارات/السيارات ----------
    application.add_handler(MessageHandler(filters.Regex(r"^شراء لقب"), cmd_buy_title))
    application.add_handler(MessageHandler(
        filters.Regex(r"^شراء (بيت|قصر|شركة|فندق)$"), cmd_buy_property
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r"^شراء سيارة( رياضية| فخمة)?$"), cmd_buy_car
    ))
    application.add_handler(MessageHandler(filters.Regex(r"^ممتلكاتي$"), cmd_my_properties))

    # ---------- توسعة الاقتصاد: الزواج الوهمي ----------
    application.add_handler(MessageHandler(filters.Regex(r"^زواج$"), cmd_marry))
    application.add_handler(MessageHandler(filters.Regex(r"^طلاق$"), cmd_divorce))
    application.add_handler(MessageHandler(filters.Regex(r"^شريك$"), cmd_partner))

    # ---------- توسعة الاقتصاد: الوظائف ----------
    application.add_handler(MessageHandler(filters.Regex(r"^وظيفة(\s+\S+)?$"), cmd_get_job))
    application.add_handler(MessageHandler(filters.Regex(r"^عمل$"), cmd_work))

    # ---------- توسعة الاقتصاد: الحظ/المقامرة/الصندوق/السرقة/الاستثمار ----------
    application.add_handler(MessageHandler(filters.Regex(r"^حظ$"), cmd_luck))
    application.add_handler(MessageHandler(filters.Regex(r"^مقامرة\s+\d+$"), cmd_gamble))
    application.add_handler(MessageHandler(filters.Regex(r"^صندوق$"), cmd_box))
    application.add_handler(MessageHandler(filters.Regex(r"^سرقة$"), cmd_steal))
    application.add_handler(MessageHandler(filters.Regex(r"^استثمار\s+\d+$"), cmd_invest))

    # ---------- الرتب ----------
    application.add_handler(MessageHandler(filters.Regex(r"^رفع\s+\S+$"), cmd_promote))
    application.add_handler(MessageHandler(filters.Regex(r"^تنزيل\s+\S+$"), cmd_demote))
    application.add_handler(MessageHandler(filters.Regex(r"^رتبة مخصصة"), cmd_set_custom_rank))

    # ---------- الألعاب ----------
    application.add_handler(MessageHandler(filters.Regex(r"^تخمين الرقم$"), cmd_start_guess_game))
    application.add_handler(MessageHandler(filters.Regex(r"^حجر ورقة مقص"), cmd_rock_paper_scissors))
    application.add_handler(MessageHandler(filters.Regex(r"^ترتيب الحروف$"), cmd_start_unscramble))
    application.add_handler(MessageHandler(filters.Regex(r"^صح أو خطأ$"), cmd_start_truefalse))
    application.add_handler(MessageHandler(filters.Regex(r"^الحساب السريع$"), cmd_start_math))
    application.add_handler(MessageHandler(filters.Regex(r"^الذاكرة$"), cmd_start_memory))
    application.add_handler(MessageHandler(filters.Regex(r"^أكمل الجملة$"), cmd_start_complete_sentence))
    application.add_handler(MessageHandler(filters.Regex(r"^(سؤال وجواب|أسرع إجابة)$"), cmd_start_quiz))

    # ---------- الاقتراحات والشكاوى ----------
    application.add_handler(MessageHandler(filters.Regex(r"^اقتراح\s+"), cmd_send_suggestion))
    application.add_handler(MessageHandler(filters.Regex(r"^شكوى\s+"), cmd_send_complaint))
    application.add_handler(CallbackQueryHandler(suggestion_callback, pattern=r"^suggestion:"))

    # ---------- النسخ الاحتياطي ----------
    application.add_handler(MessageHandler(filters.Regex(r"^نسخ احتياطي$"), cmd_backup))
    application.add_handler(MessageHandler(filters.Regex(r"^استعادة نسخة احتياطية$"), cmd_restore_instructions))
    application.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_restore_file))

    # ---------- أوامر المطور ----------
    application.add_handler(MessageHandler(filters.Regex(r"^حظر مجموعة\s+-?\d+$"), cmd_ban_group))
    application.add_handler(MessageHandler(filters.Regex(r"^فك حظر مجموعة\s+-?\d+$"), cmd_unban_group))
    application.add_handler(MessageHandler(filters.Regex(r"^تفعيل مجموعة\s+-?\d+$"), cmd_activate_group))
    application.add_handler(MessageHandler(filters.Regex(r"^تعطيل مجموعة\s+-?\d+$"), cmd_deactivate_group))
    application.add_handler(MessageHandler(filters.Regex(r"^تشغيل الذكاء الاصطناعي"), cmd_toggle_ai_on))
    application.add_handler(MessageHandler(filters.Regex(r"^ايقاف الذكاء الاصطناعي"), cmd_toggle_ai_off))
    application.add_handler(MessageHandler(filters.Regex(r"^إذاعة"), cmd_broadcast))

    # ---------- الترحيب ----------
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )
    application.add_handler(
        MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, member_left)
    )

    # ---------- أزرار Inline ----------
    application.add_handler(CallbackQueryHandler(dev_panel_callback, pattern=r"^dev:"))
    application.add_handler(CallbackQueryHandler(welcome_rules_callback, pattern=r"^welcome:"))

    # ---------- معالج الأخطاء العام ----------
    application.add_error_handler(global_error_handler)

    # ---------- المعالج العام لكل رسائل النص (يجب أن يكون الأخير) ----------
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message)
    )

    return application


def main():
    application = build_application()
    logger.info("⏳ بدء تشغيل البوت بنظام polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
