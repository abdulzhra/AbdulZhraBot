"""
توسعة نظام الاقتصاد: المتجر (ألقاب/ألوان/أوسمة) - العقارات - السيارات
الزواج الوهمي - نظام العمل - الحظ/المقامرة/الصندوق - السرقة - الاستثمار
"""
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import economy as db_eco
from database import properties as db_props

# ============== أسعار المتجر/الممتلكات ==============

TITLES_SHOP = {
    "فقير": 0,
    "غني": 1000,
    "تاجر": 3000,
    "مليونير": 10000,
    "ملياردير": 50000,
    "شيخ التجار": 150000,
}

PROPERTIES_SHOP = {
    "بيت": 2000,
    "قصر": 20000,
    "شركة": 50000,
    "فندق": 100000,
}

CARS_SHOP = {
    "سيارة": 1500,
    "سيارة رياضية": 8000,
    "سيارة فخمة": 30000,
}

JOBS = {
    "صيد": (50, 150),
    "تجارة": (100, 300),
    "مزارع": (60, 180),
    "سائق": (80, 200),
    "مبرمج": (150, 400),
}


# ============== المتجر: الألقاب ==============

async def cmd_buy_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: شراء لقب [الاسم]"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not context.args:
        items = "\n".join(f"{name} — {price} دينار" for name, price in TITLES_SHOP.items())
        await message.reply_text(f"🏷 الألقاب المتوفرة:\n\n{items}\n\nاستخدم: شراء لقب [الاسم]")
        return

    title = " ".join(context.args)
    if title not in TITLES_SHOP:
        await message.reply_text("هذا اللقب غير موجود بالمتجر.")
        return

    price = TITLES_SHOP[title]
    wallet = await db_eco.get_wallet(chat.id, user.id)
    if wallet["balance"] < price:
        await message.reply_text(f"رصيدك ما يكفي. السعر: {price} دينار جونير")
        return

    await db_eco.add_balance(chat.id, user.id, -price)
    await db_eco.set_title(chat.id, user.id, title)
    await message.reply_text(f"🏷 تم شراء لقب «{title}» مقابل {price} دينار جونير")


# ============== العقارات ==============

async def cmd_buy_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: شراء بيت / شراء قصر / شراء شركة / شراء فندق"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    item_name = message.text.replace("شراء", "").strip()
    if item_name not in PROPERTIES_SHOP:
        return

    price = PROPERTIES_SHOP[item_name]
    wallet = await db_eco.get_wallet(chat.id, user.id)
    if wallet["balance"] < price:
        await message.reply_text(f"رصيدك ما يكفي. سعر {item_name}: {price} دينار جونير")
        return

    await db_eco.add_balance(chat.id, user.id, -price)
    await db_props.add_property(chat.id, user.id, "عقار", item_name)
    await message.reply_text(f"🏠 تم شراء {item_name} مقابل {price} دينار جونير، مبروك!")


# ============== السيارات ==============

async def cmd_buy_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: شراء سيارة / شراء سيارة رياضية / شراء سيارة فخمة"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    item_name = message.text.replace("شراء", "").strip()
    if item_name not in CARS_SHOP:
        return

    price = CARS_SHOP[item_name]
    wallet = await db_eco.get_wallet(chat.id, user.id)
    if wallet["balance"] < price:
        await message.reply_text(f"رصيدك ما يكفي. سعر {item_name}: {price} دينار جونير")
        return

    await db_eco.add_balance(chat.id, user.id, -price)
    await db_props.add_property(chat.id, user.id, "سيارة", item_name)
    await message.reply_text(f"🚗 تم شراء {item_name} مقابل {price} دينار جونير، مشوار هنيء!")


async def cmd_my_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: ممتلكاتي"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    items = await db_props.get_user_properties(chat.id, user.id)
    if not items:
        await message.reply_text("ما عندك ممتلكات بعد. جرب: شراء بيت / شراء سيارة")
        return

    lines = ["🏠 ممتلكاتك:\n"]
    for item in items:
        lines.append(f"• {item['item_name']}")
    await message.reply_text("\n".join(lines))


# ============== الزواج الوهمي ==============

async def cmd_marry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: زواج - بالرد على شخص"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("لازم ترد على الشخص اللي تريد تتزوجه 😄")
        return

    target = message.reply_to_message.from_user
    if target.id == user.id:
        await message.reply_text("ما تكدر تتزوج نفسك 😂")
        return

    existing_user = await db_props.get_marriage(chat.id, user.id)
    if existing_user:
        await message.reply_text("تره انت متزوج هسة! لازم تطلق أول.")
        return

    existing_target = await db_props.get_marriage(chat.id, target.id)
    if existing_target:
        await message.reply_text(f"{target.first_name} متزوج/ة هسة، ما يكدر يتزوج مرتين 😅")
        return

    await db_props.create_marriage(chat.id, user.id, target.id)
    await message.reply_text(f"💍 مبروك! {user.first_name} و {target.first_name} صاروا متزوجين بالكروب")


async def cmd_divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: طلاق"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    existing = await db_props.get_marriage(chat.id, user.id)
    if not existing:
        await message.reply_text("انت مو متزوج أصلاً 😅")
        return

    await db_props.delete_marriage(chat.id, user.id)
    await message.reply_text(f"💔 تم الطلاق، {user.first_name} رجع أعزب/عزباء")


async def cmd_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: شريك - يعرض شريك الزواج الحالي"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    marriage = await db_props.get_marriage(chat.id, user.id)
    if not marriage:
        await message.reply_text("ما عندك شريك حالياً، جرب أمر: زواج (بالرد على شخص)")
        return

    partner_id = db_props.get_partner_id(marriage, user.id)
    try:
        partner_chat = await context.bot.get_chat(partner_id)
        name = partner_chat.full_name
    except Exception:
        name = f"مستخدم {partner_id}"
    await message.reply_text(f"💑 شريكك هو: {name}")


# ============== نظام العمل ==============

async def cmd_get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: وظيفة [صيد/تجارة/مزارع/سائق/مبرمج] أو بدون آرغيومنت لعرض القائمة"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not context.args:
        items = "\n".join(f"{name} — دخل {lo}-{hi} دينار" for name, (lo, hi) in JOBS.items())
        await message.reply_text(f"💼 الوظائف المتوفرة:\n\n{items}\n\nاستخدم: وظيفة [الاسم]")
        return

    job_name = context.args[0]
    if job_name not in JOBS:
        await message.reply_text("هذي الوظيفة غير موجودة.")
        return

    await db_eco.set_job(chat.id, user.id, job_name)
    await message.reply_text(f"💼 تم تعيينك بوظيفة: {job_name}\nاكتب: عمل، للحصول على دخلك")


async def cmd_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: عمل - يحصل المستخدم على دخل عشوائي بناءً على وظيفته الحالية"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    wallet = await db_eco.get_wallet(chat.id, user.id)
    job = wallet["job"]
    if not job or job not in JOBS:
        await message.reply_text("ما عندك وظيفة. جرب: وظيفة [صيد/تجارة/مزارع/سائق/مبرمج]")
        return

    lo, hi = JOBS[job]
    income = random.randint(lo, hi)
    await db_eco.add_balance(chat.id, user.id, income)
    await message.reply_text(f"💼 شغلت كـ {job} وحصلت على {income} دينار جونير 💰")


# ============== الحظ / المقامرة / الصندوق ==============

async def cmd_luck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: حظ - جائزة عشوائية صغيرة مجانية"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    outcomes = [0, 0, 20, 50, 100, 200, 500]
    prize = random.choice(outcomes)
    if prize == 0:
        await message.reply_text("😅 ما طلع لك شي هاي المرة، جرب بعدين")
    else:
        await db_eco.add_balance(chat.id, user.id, prize)
        await message.reply_text(f"🍀 حظك زين! فزت بـ {prize} دينار جونير")


async def cmd_gamble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: مقامرة [مبلغ] - فرصة 45% للفوز بمضاعفة المبلغ"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not context.args:
        await message.reply_text("استخدم: مقامرة [مبلغ]")
        return
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply_text("اكتب مبلغ صحيح.")
        return

    wallet = await db_eco.get_wallet(chat.id, user.id)
    if wallet["balance"] < amount:
        await message.reply_text("رصيدك ما يكفي لهذا المبلغ.")
        return

    if random.random() < 0.45:
        await db_eco.add_balance(chat.id, user.id, amount)
        await message.reply_text(f"🎲 فزت! ضاعفنا مبلغك، صار لك +{amount} دينار جونير")
    else:
        await db_eco.add_balance(chat.id, user.id, -amount)
        await message.reply_text(f"🎲 خسرت {amount} دينار جونير، حظ ثاني")


async def cmd_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: صندوق - صندوق مجاني بمكاسب عشوائية (محدد بفترة، تبسيط: بدون تبريد حالياً)"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    prize = random.randint(10, 300)
    await db_eco.add_balance(chat.id, user.id, prize)
    await message.reply_text(f"🎁 فتحت الصندوق ولقيت {prize} دينار جونير")


# ============== السرقة ==============

async def cmd_steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: سرقة - بالرد على شخص، فرصة 35% للنجاح"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("لازم ترد على الشخص اللي تريد تسرقه 🥷")
        return

    target = message.reply_to_message.from_user
    if target.id == user.id:
        await message.reply_text("ما تكدر تسرق نفسك 😂")
        return

    target_wallet = await db_eco.get_wallet(chat.id, target.id)
    if target_wallet["balance"] < 50:
        await message.reply_text("هذا الشخص فقير، ما يستاهل السرقة 😅")
        return

    if random.random() < 0.35:
        stolen = random.randint(20, min(300, target_wallet["balance"]))
        await db_eco.add_balance(chat.id, target.id, -stolen)
        await db_eco.add_balance(chat.id, user.id, stolen)
        await message.reply_text(f"🥷 نجحت السرقة! أخذت {stolen} دينار جونير من {target.first_name}")
    else:
        penalty = 50
        await db_eco.add_balance(chat.id, user.id, -penalty)
        await message.reply_text(f"🚨 فشلت السرقة وانضبطت! خسرت {penalty} دينار جونير")


# ============== الاستثمار ==============

async def cmd_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: استثمار [مبلغ] - ربح أو خسارة عشوائية بنسبة متغيرة"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not context.args:
        await message.reply_text("استخدم: استثمار [مبلغ]")
        return
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply_text("اكتب مبلغ صحيح.")
        return

    wallet = await db_eco.get_wallet(chat.id, user.id)
    if wallet["balance"] < amount:
        await message.reply_text("رصيدك ما يكفي لهذا المبلغ.")
        return

    change_percent = random.uniform(-0.5, 0.8)  # خسارة حتى 50% أو ربح حتى 80%
    result = int(amount * change_percent)
    await db_eco.add_balance(chat.id, user.id, result)

    if result >= 0:
        await message.reply_text(f"📈 استثمارك نجح! ربحت {result} دينار جونير إضافية")
    else:
        await message.reply_text(f"📉 استثمارك خسر! نزل رصيدك {abs(result)} دينار جونير")
