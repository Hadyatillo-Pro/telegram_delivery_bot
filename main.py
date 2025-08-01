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

# 1. order_start.py
@router.message(F.text.lower() == "start")
async def start_order(msg: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Somsa")], [KeyboardButton(text="Ichimlik")], [KeyboardButton(text="Sous")]], resize_keyboard=True)
    await msg.answer("Mahsulot turini tanlang:", reply_markup=markup)
    await state.set_state(OrderStates.choosing_category)

# 2. product_selection.py
@router.message(OrderStates.choosing_category)
async def select_product(msg: Message, state: FSMContext):
    category = msg.text
    await state.update_data(category=category)
    await msg.answer(f"Tanlangan kategoriya: {category}. Mahsulotni yozing:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderStates.choosing_product)

# 3. product_quantity.py
@router.message(OrderStates.choosing_product)
async def enter_quantity(msg: Message, state: FSMContext):
    product = msg.text
    await state.update_data(product=product)
    await msg.answer("Nechta buyurtma qilasiz?")
    await state.set_state(OrderStates.choosing_quantity)

# 4. payment_method.py
@router.message(OrderStates.choosing_quantity)
async def choose_payment(msg: Message, state: FSMContext):
    quantity = msg.text
    await state.update_data(quantity=quantity)
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Naqd")], [KeyboardButton(text="Karta orqali")]], resize_keyboard=True)
    await msg.answer("To'lov turini tanlang:", reply_markup=markup)
    await state.set_state(OrderStates.choosing_payment)

# 5. location_handler.py
@router.message(OrderStates.choosing_payment)
async def ask_location(msg: Message, state: FSMContext):
    payment = msg.text
    await state.update_data(payment=payment)
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Joylashuvni yuborish", request_location=True)]], resize_keyboard=True)
    await msg.answer("Iltimos, joylashuv yuboring:", reply_markup=markup)
    await state.set_state(OrderStates.sending_location)

# 6. phone_handler.py
@router.message(F.location, OrderStates.sending_location)
async def ask_phone(msg: Message, state: FSMContext):
    await state.update_data(location=msg.location)
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]], resize_keyboard=True)
    await msg.answer("Endi telefon raqamingizni yuboring:", reply_markup=markup)
    await state.set_state(OrderStates.sending_phone)

# 7. confirmation_handler.py
@router.message(F.contact, OrderStates.sending_phone)
async def confirm_order(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.contact.phone_number)
    data = await state.get_data()
    summary = (
        f"\u2709\ufe0f Buyurtma:\n"
        f"Kategoriya: {kategoriya}\n"
        f"Mahsulot: {mahsulot}\n"
        f"Soni: {soni}\n"
        f"To‘lov: {tolov}\n"
        f"Manzil: {manzil}\n"
        f"Telefon: {telefon}"
    )
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Tasdiqlash")], [KeyboardButton(text="Bekor qilish")]], resize_keyboard=True)
    await msg.answer(summary, reply_markup=markup)
    await state.set_state(OrderStates.confirming_order)

# 8. cancel_handler.py
@router.message(F.text == "Bekor qilish", OrderStates.confirming_order)
async def cancel(msg: Message, state: FSMContext):
    await msg.answer("Buyurtma bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@router.message(F.text == "Tasdiqlash", OrderStates.confirming_order)
async def done(msg: Message, state: FSMContext):
    await msg.answer("✅ Buyurtma qabul qilindi!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
