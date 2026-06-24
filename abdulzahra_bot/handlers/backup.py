"""
نظام النسخ الاحتياطي (تصدير/استيراد JSON لأهم الجداول) + تسجيل الأخطاء
متاح فقط للمطور
"""
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_pool
from utils.permissions import is_developer

logger = logging.getLogger(__name__)

BACKUP_TABLES = ["users", "groups", "group_members", "wallets", "auto_replies"]


async def log_error_to_db(error_text: str, context_info: str = ""):
    """يُستدعى من أي مكان بالبوت لتسجيل خطأ بقاعدة البيانات"""
    try:
        pool = get_pool()
        await pool.execute(
            "INSERT INTO error_logs (error_text, context) VALUES ($1, $2)",
            error_text, context_info,
        )
    except Exception:
        logger.exception("فشل تسجيل الخطأ بقاعدة البيانات")


async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: نسخ احتياطي - يصدّر كل الجداول الأساسية كملف JSON ويرسله بالخاص"""
    message = update.effective_message
    user = update.effective_user

    if not is_developer(user.id):
        await message.reply_text("هذا الأمر للمطور فقط 🚫")
        return

    pool = get_pool()
    backup_data = {}

    for table in BACKUP_TABLES:
        rows = await pool.fetch(f"SELECT * FROM {table}")
        backup_data[table] = [dict(row) for row in rows]

    # تحويل أي قيم تاريخ لنص لكي تكون قابلة لـ JSON
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    json_bytes = json.dumps(backup_data, default=default_serializer, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    await context.bot.send_document(
        chat_id=user.id,
        document=json_bytes,
        filename=filename,
        caption="📦 نسخة احتياطية من قاعدة البيانات",
    )
    await message.reply_text("✅ تم إرسال النسخة الاحتياطية لخاصك")


async def cmd_restore_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: استعادة نسخة احتياطية - يطلب من المطور رفع ملف JSON كرد"""
    message = update.effective_message
    user = update.effective_user

    if not is_developer(user.id):
        await message.reply_text("هذا الأمر للمطور فقط 🚫")
        return

    await message.reply_text(
        "📥 لاستعادة نسخة احتياطية، أرسل ملف الـ JSON الآن كرد على هذي الرسالة."
    )


async def handle_restore_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى عند استقبال ملف من المطور بالخاص - يحاول استعادة البيانات منه"""
    message = update.effective_message
    user = update.effective_user

    if not is_developer(user.id):
        return
    if not message.document or not message.document.file_name.endswith(".json"):
        return

    file = await context.bot.get_file(message.document.file_id)
    file_bytes = await file.download_as_bytearray()
    data = json.loads(file_bytes.decode("utf-8"))

    pool = get_pool()
    restored_counts = {}

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                for table, rows in data.items():
                    if table not in BACKUP_TABLES or not rows:
                        continue
                    columns = list(rows[0].keys())
                    for row in rows:
                        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
                        col_names = ", ".join(columns)
                        update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns)
                        conflict_key = _primary_key_for(table)
                        query = (
                            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
                            f"ON CONFLICT ({conflict_key}) DO UPDATE SET {update_clause}"
                        )
                        values = [row[c] for c in columns]
                        await conn.execute(query, *values)
                    restored_counts[table] = len(rows)

        await message.reply_text(f"✅ تمت الاستعادة بنجاح:\n{restored_counts}")
    except Exception as e:
        logger.exception("فشل استعادة النسخة الاحتياطية")
        await message.reply_text(f"❌ فشلت الاستعادة: {e}")


def _primary_key_for(table: str) -> str:
    mapping = {
        "users": "user_id",
        "groups": "group_id",
        "group_members": "group_id, user_id",
        "wallets": "group_id, user_id",
        "auto_replies": "id",
    }
    return mapping.get(table, "id")
