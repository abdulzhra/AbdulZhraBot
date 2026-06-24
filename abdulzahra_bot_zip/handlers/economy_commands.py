"""
أوامر نظام الاقتصاد: فلوسي/رصيدي/محفظتي - راتب - إيداع/سحب - تحويل
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import economy as db_eco


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: فلوسي / رصيدي / محفظتي"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    wallet = await db_eco.get_wallet(chat.id, user.id)
    text = (
        f"💰 محفظة {user.first_name}\n\n"
        f"💵 الرصيد: {wallet['balance']} دينار جونير\n"
        f"🏦 رصيد البنك: {wallet['bank_balance']} دينار جونير\n"
        f"🏷 اللقب: {wallet['title']}"
    )
    await message.reply_text(text)


async def cmd_daily_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: راتب"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    success, value = await db_eco.claim_daily_salary(chat.id, user.id)
    if success:
        await message.reply_text(f"✅ استلمت راتبك اليومي: {value} دينار جونير 💰")
    else:
        await message.reply_text(f"⏳ تره استلمت راتبك اليوم. تعال بعد {value} ساعة تقريباً.")


async def cmd_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: ايداع [مبلغ]"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    amount = _parse_amount(context.args)
    if amount is None:
        await message.reply_text("اكتب المبلغ صحيح، مثلاً: ايداع 100")
        return

    success = await db_eco.deposit_to_bank(chat.id, user.id, amount)
    if success:
        await message.reply_text(f"🏦 تم إيداع {amount} دينار جونير بالبنك.")
    else:
        await message.reply_text("رصيدك ما يكفي لهذا المبلغ.")


async def cmd_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: سحب [مبلغ]"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    amount = _parse_amount(context.args)
    if amount is None:
        await message.reply_text("اكتب المبلغ صحيح، مثلاً: سحب 100")
        return

    success = await db_eco.withdraw_from_bank(chat.id, user.id, amount)
    if success:
        await message.reply_text(f"💵 تم سحب {amount} دينار جونير من البنك.")
    else:
        await message.reply_text("رصيد البنك ما يكفي لهذا المبلغ.")


async def cmd_bank_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: رصيد البنك"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    wallet = await db_eco.get_wallet(chat.id, user.id)
    await message.reply_text(f"🏦 رصيدك بالبنك: {wallet['bank_balance']} دينار جونير")


async def cmd_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: تحويل [مبلغ] - يجب أن يكون بالرد على شخص آخر"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("لازم ترد على الشخص اللي تريد تحوله الفلوس.")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == user.id:
        await message.reply_text("ما يمكن تحول فلوس لنفسك 😅")
        return

    amount = _parse_amount(context.args)
    if amount is None:
        await message.reply_text("اكتب المبلغ صحيح، مثلاً: تحويل 100 (بالرد على شخص)")
        return

    success = await db_eco.transfer_balance(chat.id, user.id, target_user.id, amount)
    if success:
        await message.reply_text(
            f"✅ تم تحويل {amount} دينار جونير من {user.first_name} إلى {target_user.first_name}"
        )
    else:
        await message.reply_text("رصيدك ما يكفي لهذا التحويل.")


def _parse_amount(args: list[str]) -> int | None:
    if not args:
        return None
    try:
        amount = int(args[0])
        if amount <= 0:
            return None
        return amount
    except (ValueError, IndexError):
        return None
