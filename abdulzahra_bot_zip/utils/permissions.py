"""
نظام الرتب والصلاحيات
يحدد الترتيب الهرمي للرتب ومن يملك صلاحية ترقية/تنزيل من
"""
from config.settings import DEVELOPER_ID

# الترتيب الهرمي من الأعلى للأدنى
RANK_HIERARCHY = [
    "المنشئ الأساسي",
    "المالك",
    "المدير",
    "الأدمن",
    "المشرف",
    "المميز",
    "عضو",
]


def rank_level(rank: str) -> int:
    """رقم أصغر = رتبة أعلى. يرجع أكبر رقم (أدنى رتبة) إذا كانت الرتبة غير معروفة."""
    try:
        return RANK_HIERARCHY.index(rank)
    except ValueError:
        return len(RANK_HIERARCHY) - 1


def can_promote(actor_rank: str, target_current_rank: str, new_rank: str) -> bool:
    """
    يتحقق إن كان actor_rank يملك صلاحية تغيير رتبة شخص من target_current_rank إلى new_rank.
    القاعدة: لا يمكنك ترقية/تنزيل أحد لرتبة مساوية أو أعلى من رتبتك.
    """
    actor_level = rank_level(actor_rank)
    target_level = rank_level(target_current_rank)
    new_level = rank_level(new_rank)

    if actor_level >= target_level:
        return False  # لا يمكن التحكم برتبة مساوية أو أعلى من رتبتك
    if actor_level >= new_level:
        return False  # لا يمكن إعطاء رتبة أعلى من أو تساوي رتبتك
    return True


def is_developer(user_id: int) -> bool:
    """يتحقق إن كان المستخدم هو المطور (المنشئ الأساسي) صاحب الـ ID الثابت"""
    return user_id == DEVELOPER_ID
