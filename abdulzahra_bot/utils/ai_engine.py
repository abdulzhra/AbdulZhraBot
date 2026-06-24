"""
محرك شخصية "جونير" - الذكاء الاصطناعي الخاص بالبوت
يستخدم Anthropic Claude API، يحافظ على سياق المحادثة لكل مجموعة،
ويرفض الأسئلة الطويلة بردود ساخرة عشوائية بدل اللجوء فعلياً للذكاء الاصطناعي.
"""
import random
import logging
from anthropic import AsyncAnthropic
from config.settings import ANTHROPIC_API_KEY, AI_MODEL, AI_CONTEXT_HISTORY_LIMIT
from database.connection import get_pool

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# عبارات الرفض العشوائية عندما يطلب المستخدم بحثاً/مقالاً/شرحاً طويلاً
LONG_REQUEST_REJECTIONS = [
    "هواي تتأمر انت 😏",
    "روح ابحث بكوكل 🔍",
    "مو كلشي ينسأل",
    "شوفلك منصة ذكاء اصطناعي ثانية",
    "هاي مو مدرسة 📚",
    "سؤالك أطول من شارع",
    "اختصرها شوية يا چم",
    "تره مو موظف يمك",
]

# كلمات مفتاحية تدل على طلب طويل/بحث/مقال
LONG_REQUEST_KEYWORDS = [
    "بحث", "مقال", "اشرح", "شرح", "اكتب لي موضوع", "موضوع كامل",
    "تقرير", "بحث كامل", "ملخص كتاب", "خطة كاملة", "اكتب قصة طويلة",
    "اشرحلي بالتفصيل", "حلل لي", "اكتب لي مقالة",
]

SYSTEM_PROMPT = """
انت اسمك "جونير"، بوت عراقي بشخصية ساخرة وخفيفة داخل كروبات تيليغرام.

قواعدك الصارمة:
- تحجي باللهجة العراقية فقط (مثل: شلونك، شصار، زين، خوش، هواي، چم، شكو ماكو).
- ردودك قصيرة جداً جداً، سطر أو سطرين بحد أقصى. لا تكتب فقرات.
- أسلوبك ساخر، خفيف، ومرح، بدون إهانة أو إساءة فعلية لأي شخص.
- لا تكتب أي شرح طويل أو مقالات أو أبحاث حتى لو طلب المستخدم.
- لا تستخدم لغة فصحى رسمية أبداً.
- لا تكرر نفس الجملة بنفس الصيغة دائماً، نوّع بأسلوبك.
- تعرف سياق المحادثة السابقة بالكروب وتتفاعل بناءً عليه.
"""


def _looks_like_long_request(text: str) -> bool:
    """يتحقق إن كان السؤال يحتوي كلمات تدل على طلب بحث/شرح طويل"""
    lowered = text.lower()
    return any(keyword in lowered for keyword in LONG_REQUEST_KEYWORDS)


async def save_message_to_history(group_id: int, user_id: int | None, role: str, content: str):
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO ai_conversation_history (group_id, user_id, role, content)
        VALUES ($1, $2, $3, $4)
        """,
        group_id, user_id, role, content,
    )
    # تنظيف الرسائل القديمة، نحتفظ فقط بآخر N رسالة لكل مجموعة
    await pool.execute(
        """
        DELETE FROM ai_conversation_history
        WHERE group_id = $1
        AND id NOT IN (
            SELECT id FROM ai_conversation_history
            WHERE group_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        )
        """,
        group_id, AI_CONTEXT_HISTORY_LIMIT,
    )


async def get_conversation_history(group_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT role, content FROM ai_conversation_history
        WHERE group_id = $1
        ORDER BY created_at ASC
        LIMIT $2
        """,
        group_id, AI_CONTEXT_HISTORY_LIMIT,
    )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


async def get_junior_reply(group_id: int, user_id: int, user_name: str, question: str) -> str:
    """
    الدالة الرئيسية: تأخذ سؤال المستخدم وترجع رد جونير.
    إذا كان السؤال يبدو كطلب بحث/شرح طويل، ترجع رداً ساخراً جاهزاً بدون استدعاء AI.
    """
    if _looks_like_long_request(question):
        return random.choice(LONG_REQUEST_REJECTIONS)

    history = await get_conversation_history(group_id)

    messages = history + [{"role": "user", "content": f"{user_name}: {question}"}]

    try:
        response = await client.messages.create(
            model=AI_MODEL,
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        reply_text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()

        if not reply_text:
            reply_text = random.choice(LONG_REQUEST_REJECTIONS)

    except Exception as e:
        logger.error(f"خطأ في استدعاء Anthropic API: {e}")
        reply_text = "صار خراب بالنظام، جرب بعد شوية 🔧"

    await save_message_to_history(group_id, user_id, "user", f"{user_name}: {question}")
    await save_message_to_history(group_id, None, "assistant", reply_text)

    return reply_text


def get_random_idle_comment() -> str:
    """تعليق عشوائي يرسله البوت من نفسه أحياناً بدون تفعيل من أحد"""
    comments = [
        "شكو ماكو 👀",
        "جاي أراقبكم 😏",
        "وين الناس؟",
        "شكلها سوالف قوية هذي",
        "محد ينام 😴",
        "استمروا، الجو زين",
        "الكروب هادئ اليوم 🤫",
    ]
    return random.choice(comments)
