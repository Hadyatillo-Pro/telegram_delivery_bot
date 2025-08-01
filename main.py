# main.py
# main.py (aiogram 3.x versiyasiga moslashtirilgan)
import asyncio
import logging
import os
from math import ceil
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

# Load .env
load_dotenv()
API_TOKEN = os.getenv("7560492080:AAGwRdJpU2P4dZgv4SwTQSMR_zXoLLFGqD8")
logging.basicConfig(level=logging.INFO)

bot = Bot(token="7560492080:AAGwRdJpU2P4dZgv4SwTQSMR_zXoLLFGqD8", parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

ADMINS = [6057841081, 6668584870, 6590535774, 24847201, 5377259476]
MIN_ORDER_AMOUNT = 50000
WORK_HOURS = (8, 19)

products = {
    'Somsa': {
        "Go'shtli Somsa": 12000,
        "Kartoshkali-Go'shtli Somsa": 10000,
        "Ovoshnoy Somsa": 10000,
        "Tovuq-Pishloqli Somsa": 8000,
        "Karto'shkali Somsa": 8000,
        "Qovoqli Somsa": 6000,
    },
    'Ichimlik': {
        "Kompo't (1 litr)": 15000,
        "Kompo't (0.5 litr)": 8000,
        "Coca-Cola (0.25 litr)": 4000,
        "Coca-Cola (0.5 litr)": 8000,
        "Coca-Cola (1.0 litr)": 12000,
        "Coca-Cola (1.5 litr)": 15000,
        "Fanta-Nok ta'mli (0.5 litr)": 8000,
        "Fanta-Apelsin ta'mli (0.5 litr)": 8000,
        "Fanta-Apelsin ta'mli (1.0 litr)": 12000,
        "Fanta-Apelsin ta'mli (1.5 litr)": 15000,
        "Fuse-tea (0.5 litr)": 10000,
        "Fuse-tea (1.0 litr)": 12000,
        "Gazlanmagan Suv (0.5 litr)": 4000,
        "Gazlanmagan Suv (1.5 litr)": 6000,
        "Gazlangan Suv (0.5 litr)": 4000,
        "Gazlangan Suv (1.5 litr)": 6000,
    },
    'Sous': {
        "Sous (0.33 litr)": 5000
    }
}

class OrderState(StatesGroup):
    choosing_product = State()
    choosing_quantity = State()
    choosing_payment = State()
    sending_location = State()
    sending_contact = State()
    confirming = State()

user_cart = {}

@router.message(F.text.in_(["Zakaz qilishni boshlash", "/start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    now = (datetime.utcnow() + timedelta(hours=5)).hour
    if message.from_user.id not in ADMINS and not (WORK_HOURS[0] <= now < WORK_HOURS[1]):
        await message.answer("Kechirasiz, buyurtmalar faqat soat 8:00 dan 19:00 gacha qabul qilinadi.")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(cat)] for cat in products])
    kb.add(KeyboardButton("❌ Buyurtmani bekor qilish"))
    await message.answer("Mahsulot kategoriyasini tanlang:", reply_markup=kb)
    user_cart[message.from_user.id] = []
    await state.set_state(OrderState.choosing_product)

@router.message(OrderState.choosing_product, F.text.in_(products))
async def show_products(message: types.Message, state: FSMContext):
    category = message.text
    kb = InlineKeyboardMarkup()
    for name, price in products[category].items():
        kb.add(InlineKeyboardButton(text=f"{name} - {price} so'm", callback_data=name))
    await message.answer("Mahsulotni tanlang:", reply_markup=kb)

@router.callback_query(OrderState.choosing_product)
async def select_product(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected_product=call.data)
    await call.message.answer(f"Nechta '{call.data}' istaysiz?, pastga sonini yozing masalan: 3")
    await state.set_state(OrderState.choosing_quantity)

@router.message(OrderState.choosing_quantity, F.text.regexp("^\\d+$"))
async def add_to_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data['selected_product']
    qty = int(message.text)
    user_cart[message.from_user.id].append((product, qty))
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton("Yakunlash"), KeyboardButton("Yana qo'shish")],
        [KeyboardButton("❌ Buyurtmani bekor qilish")]
    ])
    await message.answer("Buyurtmangizga qo‘shildi. Yana mahsulot qo‘shasizmi yoki yakunlaysizmi?", reply_markup=kb)

# ... Qolgan handlerlar ham xuddi shunday tarzda moslashtiriladi

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
