
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any
from utils.time_check import is_working_time, is_admin

class WorkingHoursMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        if is_admin(user_id) or is_working_time():
            return await handler(event, data)
        else:
            await event.answer(
                "🕗 Kechirasiz, ish vaqti 8:00 dan 19:00 gacha.\n\n"
                "Agar vaqt 20:30 dan o'tmagan bo'lsa, iltimos @Hadyatillo25 ga murojaat qiling."
            )
            return
