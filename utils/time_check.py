# utils/time_check.py
from datetime import datetime

ADMINS = [6057841081, 6668584870, 6590535774, 24847201]

def is_working_time() -> bool:
    now = datetime.now().time()
    return now >= datetime.strptime("08:00", "%H:%M").time() and now <= datetime.strptime("19:00", "%H:%M").time()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS
