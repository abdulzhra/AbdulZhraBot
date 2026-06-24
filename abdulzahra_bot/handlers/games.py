"""
نظام الألعاب: تخمين الرقم + حجر ورقة مقص
مصمم بشكل قابل للتوسعة لإضافة باقي الألعاب (ترتيب الحروف، صح أو خطأ...) بنفس النمط
"""
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import users as db_users
from database import economy as db_eco

# تخزين مؤقت في الذاكرة لألعاب تخمين الرقم الجارية، المفتاح هو (group_id)
_active_guess_games: dict[int, int] = {}

GAME_REWARD_POINTS = 20
GAME_REWARD_MONEY = 50


async def cmd_start_guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: تخمين الرقم - يبدأ لعبة تخمين رقم بين 1 و 50"""
    chat = update.effective_chat
    message = update.effective_message

    if not await db_users.is_group_active(chat.id):
        return

    if chat.id in _active_guess_games:
        await message.reply_text("تره فيه لعبة شغالة هسة بالكروب! خمن الرقم 🎯")
        return

    secret_number = random.randint(1, 50)
    _active_guess_games[chat.id] = secret_number

    await message.reply_text(
        "🎯 لعبة تخمين الرقم!\n\n"
        "فكرت برقم بين 1 و 50.\n"
        "اكتب رقمك بالرد على هذي الرسالة... يلا منو يلحقها!"
    )


async def handle_guess_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى من المعالج الرئيسي للرسائل للتحقق إن كانت الرسالة تخمين رقم صحيح"""
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_guess_games:
        return False
    if not message.text or not message.text.strip().isdigit():
        return False

    guess = int(message.text.strip())
    secret = _active_guess_games[chat.id]

    if guess == secret:
        del _active_guess_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=GAME_REWARD_POINTS, xp=10)
        await db_eco.add_balance(chat.id, user.id, GAME_REWARD_MONEY)
        await message.reply_text(
            f"🎉 صحيح! الرقم كان {secret}\n"
            f"مبروك {user.first_name}، فزت بـ {GAME_REWARD_POINTS} نقطة و {GAME_REWARD_MONEY} دينار جونير 💰"
        )
        return True
    elif guess < secret:
        await message.reply_text("⬆️ أعلى من هذا")
        return True
    else:
        await message.reply_text("⬇️ أقل من هذا")
        return True


async def cmd_rock_paper_scissors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: حجر ورقة مقص [اختيارك]"""
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    choices = {"حجر": "✊", "ورقة": "✋", "مقص": "✌️"}

    if not context.args or context.args[0] not in choices:
        await message.reply_text("اكتب اختيارك: حجر ورقة مقص [حجر/ورقة/مقص]")
        return

    user_choice = context.args[0]
    bot_choice = random.choice(list(choices.keys()))

    result_text = f"أنت: {choices[user_choice]} {user_choice}\nجونير: {choices[bot_choice]} {bot_choice}\n\n"

    if user_choice == bot_choice:
        result_text += "🤝 تعادل!"
    elif (
        (user_choice == "حجر" and bot_choice == "مقص") or
        (user_choice == "ورقة" and bot_choice == "حجر") or
        (user_choice == "مقص" and bot_choice == "ورقة")
    ):
        result_text += f"🎉 فزت يا {user.first_name}!"
        await db_users.increment_member_activity(chat.id, user.id, points=10, xp=5)
        await db_eco.add_balance(chat.id, user.id, 25)
    else:
        result_text += "😅 خسرت، حظ ثاني"

    await message.reply_text(result_text)


# ============== ترتيب الحروف ==============

_active_unscramble_games: dict[int, str] = {}  # group_id -> الكلمة الصحيحة

WORD_BANK = ["كتاب", "حاسوب", "مدرسة", "سيارة", "قمر", "بحر", "جبل", "وردة", "بيت", "نجمة"]


async def cmd_start_unscramble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: ترتيب الحروف - يعرض حروف كلمة مبعثرة ويطلب ترتيبها"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_unscramble_games:
        await message.reply_text("تره فيه لعبة شغالة هسة! رتب الحروف 🔤")
        return

    word = random.choice(WORD_BANK)
    letters = list(word)
    random.shuffle(letters)
    _active_unscramble_games[chat.id] = word

    await message.reply_text(
        f"🔤 رتب الحروف: {' - '.join(letters)}\n\nاكتب الكلمة الصحيحة!"
    )


async def handle_unscramble_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_unscramble_games or not message.text:
        return False

    correct_word = _active_unscramble_games[chat.id]
    if message.text.strip() == correct_word:
        del _active_unscramble_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=GAME_REWARD_POINTS, xp=10)
        await db_eco.add_balance(chat.id, user.id, GAME_REWARD_MONEY)
        await message.reply_text(
            f"🎉 صحيح! الكلمة كانت «{correct_word}»\n"
            f"مبروك {user.first_name}، فزت بـ {GAME_REWARD_POINTS} نقطة و {GAME_REWARD_MONEY} دينار جونير 💰"
        )
        return True
    return False


# ============== صح أو خطأ ==============

_active_truefalse_games: dict[int, bool] = {}

TRUE_FALSE_QUESTIONS = [
    ("الشمس تشرق من الغرب", False),
    ("بغداد عاصمة العراق", True),
    ("الماء يتجمد عند 0 درجة سيليزيوس", True),
    ("القطة من الزواحف", False),
    ("الأرض تدور حول الشمس", True),
    ("عدد أيام السنة 365 يوم تقريباً", True),
]


async def cmd_start_truefalse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: صح أو خطأ"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_truefalse_games:
        await message.reply_text("تره فيه سؤال شغال هسة! جاوب عليه أول 🤔")
        return

    question, answer = random.choice(TRUE_FALSE_QUESTIONS)
    _active_truefalse_games[chat.id] = answer

    await message.reply_text(f"❓ {question}\n\nصح أو خطأ؟")


async def handle_truefalse_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_truefalse_games or not message.text:
        return False

    text = message.text.strip()
    if text not in ("صح", "خطأ"):
        return False

    correct_answer = _active_truefalse_games[chat.id]
    user_said_true = (text == "صح")

    del _active_truefalse_games[chat.id]

    if user_said_true == correct_answer:
        await db_users.increment_member_activity(chat.id, user.id, points=15, xp=8)
        await db_eco.add_balance(chat.id, user.id, 30)
        await message.reply_text(f"✅ إجابة صحيحة! مبروك {user.first_name} 🎉")
    else:
        await message.reply_text("❌ إجابة خاطئة، حظ ثاني")
    return True


# ============== الحساب السريع ==============

_active_math_games: dict[int, int] = {}


async def cmd_start_math(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: الحساب السريع"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_math_games:
        await message.reply_text("تره فيه عملية حساب شغالة هسة! 🔢")
        return

    a, b = random.randint(1, 50), random.randint(1, 50)
    operator = random.choice(["+", "-", "*"])
    answer = {"+": a + b, "-": a - b, "*": a * b}[operator]

    _active_math_games[chat.id] = answer
    await message.reply_text(f"🔢 حل بسرعة: {a} {operator} {b} = ؟")


async def handle_math_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_math_games or not message.text:
        return False
    text = message.text.strip()
    if not (text.lstrip("-").isdigit()):
        return False

    correct_answer = _active_math_games[chat.id]
    if int(text) == correct_answer:
        del _active_math_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=15, xp=8)
        await db_eco.add_balance(chat.id, user.id, 30)
        await message.reply_text(f"⚡ صحيح وبسرعة! مبروك {user.first_name} 🎉")
        return True
    return False


# ============== الذاكرة (تذكر تسلسل أرقام) ==============

_active_memory_games: dict[int, str] = {}


async def cmd_start_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: الذاكرة - يعرض تسلسل أرقام لثواني ثم يطلب كتابته"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_memory_games:
        await message.reply_text("تره فيه لعبة ذاكرة شغالة هسة! 🧠")
        return

    sequence = " ".join(str(random.randint(0, 9)) for _ in range(5))
    _active_memory_games[chat.id] = sequence.replace(" ", "")

    await message.reply_text(f"🧠 احفظ هذا التسلسل: {sequence}\n\nاكتبه بسرعة بدون فواصل!")


async def handle_memory_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_memory_games or not message.text:
        return False

    correct_sequence = _active_memory_games[chat.id]
    if message.text.strip() == correct_sequence:
        del _active_memory_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=20, xp=10)
        await db_eco.add_balance(chat.id, user.id, 40)
        await message.reply_text(f"🧠 ذاكرة قوية! مبروك {user.first_name} 🎉")
        return True
    return False


# ============== أكمل الجملة ==============

_active_complete_games: dict[int, str] = {}

SENTENCE_BANK = [
    ("الصبر مفتاح ___", "الفرج"),
    ("العلم نور و___ ظلام", "الجهل"),
    ("من جد ___", "وجد"),
    ("اليد الواحدة ما ___", "تصفق"),
]


async def cmd_start_complete_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: أكمل الجملة"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_complete_games:
        await message.reply_text("تره فيه جملة شغالة هسة! 📝")
        return

    sentence, answer = random.choice(SENTENCE_BANK)
    _active_complete_games[chat.id] = answer

    await message.reply_text(f"📝 أكمل الجملة:\n\n{sentence}")


async def handle_complete_sentence_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_complete_games or not message.text:
        return False

    correct_answer = _active_complete_games[chat.id]
    if message.text.strip() == correct_answer:
        del _active_complete_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=15, xp=8)
        await db_eco.add_balance(chat.id, user.id, 30)
        await message.reply_text(f"📝 صحيح! مبروك {user.first_name} 🎉")
        return True
    return False


# ============== أسرع إجابة (أسئلة عامة) ==============

_active_quiz_games: dict[int, str] = {}

QUIZ_BANK = [
    ("عاصمة مصر؟", "القاهرة"),
    ("أكبر كوكب بالمجموعة الشمسية؟", "المشتري"),
    ("عدد قارات العالم؟", "7"),
    ("لغة برمجة شائعة اسمها ثعبان بالإنجليزية؟", "بايثون"),
]


async def cmd_start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر: سؤال وجواب  /  أسرع إجابة"""
    chat = update.effective_chat
    message = update.effective_message

    if chat.id in _active_quiz_games:
        await message.reply_text("تره فيه سؤال شغال هسة! 🙋")
        return

    question, answer = random.choice(QUIZ_BANK)
    _active_quiz_games[chat.id] = answer

    await message.reply_text(f"🙋 {question}")


async def handle_quiz_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.id not in _active_quiz_games or not message.text:
        return False

    correct_answer = _active_quiz_games[chat.id]
    if message.text.strip() == correct_answer:
        del _active_quiz_games[chat.id]
        await db_users.increment_member_activity(chat.id, user.id, points=15, xp=8)
        await db_eco.add_balance(chat.id, user.id, 30)
        await message.reply_text(f"🙋 جواب صحيح! مبروك {user.first_name} 🎉")
        return True
    return False


# ============== دالة موحّدة تُستدعى من المعالج الرئيسي ==============

async def handle_any_game_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    تتحقق بالترتيب من كل الألعاب التي تنتظر رداً نصياً بهذي المجموعة.
    تُستدعى من handlers/messages.py قبل باقي المعالجة.
    """
    if await handle_guess_attempt(update, context):
        return True
    if await handle_unscramble_attempt(update, context):
        return True
    if await handle_truefalse_attempt(update, context):
        return True
    if await handle_math_attempt(update, context):
        return True
    if await handle_memory_attempt(update, context):
        return True
    if await handle_complete_sentence_attempt(update, context):
        return True
    if await handle_quiz_attempt(update, context):
        return True
    return False

