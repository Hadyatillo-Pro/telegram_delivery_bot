# main.py
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from math import ceil
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("7560492080:AAFiVVLp_pe0R7wpYPPDwlZdLgGmmPX9e7c")

logging.basicConfig(level=logging.INFO)

bot = Bot(token="7560492080:AAFiVVLp_pe0R7wpYPPDwlZdLgGmmPX9e7c")
dp = Dispatcher(bot, storage=MemoryStorage())

ADMINS = [6057841081, 6668584870, 6590535774, 24847201, 5377259476]
MIN_ORDER_AMOUNT = 50000
BASE_DELIVERY_COST = 15000
EXTRA_KM_COST = 2000
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

@dp.message_handler(lambda msg: msg.text == "Zakaz qilishni boshlash")
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    now = (datetime.utcnow() + timedelta(hours=5)).hour
    if message.from_user.id not in ADMINS and not (WORK_HOURS[0] <= now < WORK_HOURS[1]):
        await message.answer("Kechirasiz, buyurtmalar faqat soat 8:00 dan 19:00 gacha qabul qilinadi.")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in products:
        kb.add(cat)
    kb.add("❌ Buyurtmani bekor qilish")
    await message.answer("Mahsulot kategoriyasini tanlang:", reply_markup=kb)
    user_cart[message.from_user.id] = []
    await OrderState.choosing_product.set()

@dp.message_handler(lambda msg: msg.text in products, state=OrderState.choosing_product)
async def show_products(message: types.Message, state: FSMContext):
    category = message.text
    kb = InlineKeyboardMarkup()
    for name, price in products[category].items():
        kb.add(InlineKeyboardButton(f"{name} - {price} so'm", callback_data=name))
    await message.answer("Mahsulotni tanlang:", reply_markup=kb)

@dp.callback_query_handler(state=OrderState.choosing_product)
async def select_product(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected_product=call.data)
    await call.message.answer(f"Nechta '{call.data}' istaysiz?,pastga sonini yozing masalan:3")
    await OrderState.next()

@dp.message_handler(lambda msg: msg.text.isdigit(), state=OrderState.choosing_quantity)
async def add_to_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product = data['selected_product']
    qty = int(message.text)
    user_cart[message.from_user.id].append((product, qty))
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Yakunlash", "Yana qo'shish", "❌ Buyurtmani bekor qilish")
    await message.answer("Buyurtmangizga qo‘shildi. Yana mahsulot qo‘shasizmi yoki yakunlaysizmi?", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text == "Yana qo'shish", state=OrderState.choosing_quantity)
async def back_to_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in products:
        kb.add(cat)
    await message.answer("Kategoriya tanlang:", reply_markup=kb)
    await OrderState.choosing_product.set()

@dp.message_handler(lambda msg: msg.text == "Yakunlash", state=OrderState.choosing_quantity)
async def choose_payment(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Naqd", "Click/Payme", "❌ Buyurtmani bekor qilish")
    await message.answer("To‘lov usulini tanlang:", reply_markup=kb)
    await OrderState.choosing_payment.set()

@dp.message_handler(lambda msg: msg.text in ["Naqd", "Click/Payme"], state=OrderState.choosing_payment)
async def get_location(message: types.Message, state: FSMContext):
    await state.update_data(payment_method=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("❌ Buyurtmani bekor qilish")
    await message.answer("Iltimos, lokatsiyangizni yuboring:", reply_markup=kb)
    await OrderState.sending_location.set()

@dp.message_handler(content_types=types.ContentType.LOCATION, state=OrderState.sending_location)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(location=message.location)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True))
    kb.add("❌ Buyurtmani bekor qilish")
    await message.answer("Endi telefon raqamingizni yuboring:", reply_markup=kb)
    await OrderState.sending_contact.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderState.sending_contact)
async def confirm_order(message: types.Message, state: FSMContext):
    cart = user_cart.get(message.from_user.id, [])
    data = await state.get_data()
    payment = data['payment_method']
    location = data['location']
    phone = message.contact.phone_number

    total = sum(
        products[cat][prod] * qty
        for prod, qty in cart
        for cat in products
        if prod in products[cat]
    )

    if total < MIN_ORDER_AMOUNT:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Yana qo'shish", "Menyuga qaytish")
        await message.answer(
            f"Minimal buyurtma miqdori {MIN_ORDER_AMOUNT} so‘m. Sizning buyurtmangiz: {total} so‘m.",
            reply_markup=kb
        )
        await OrderState.choosing_quantity.set()
        return

    order_text = "\n".join([f"{p} x {q}" for p, q in cart])
    full_text = (
        f"📦 Sizning buyurtmangiz:\n\n"
        f"🧾 {order_text}\n"
        f"💰 To‘lov usuli: {payment}\n"
        f"📞 Telefon: {phone}\n"
        f"💵 Umumiy summa: {total} so‘m\n\n"
        f"Iltimos, buyurtmani tasdiqlang, o‘zgartiring yoki bekor qiling."
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Tasdiqlash", "✏️ O‘zgartirish", "❌ Bekor qilish")
    await message.answer(full_text, reply_markup=kb)
    await state.update_data(phone=phone)
    await OrderState.confirming.set()

@dp.message_handler(lambda msg: msg.text == "✅ Tasdiqlash", state=OrderState.confirming)
async def send_order_to_admins(message: types.Message, state: FSMContext):
    cart = user_cart.get(message.from_user.id, [])
    data = await state.get_data()
    payment = data['payment_method']
    location = data['location']
    phone = data['phone']

    order_text = "\n".join([f"{p} x {q}" for p, q in cart])
    total = sum(products[cat][prod] * qty for prod, qty in cart for cat in products if prod in products[cat])

    full_text = (
        f"🆕 Yangi buyurtma!\n\n"
        f"👤 Foydalanuvchi: @{message.from_user.username or message.from_user.full_name}\n"
        f"📞 Telefon: {phone}\n"
        f"📦 Buyurtma:\n{order_text}\n"
        f"💰 To‘lov: {payment}\n"
        f"🧾 Umumiy: {total} so‘m"
    )

    for admin in ADMINS:
        try:
            await bot.send_message(admin, full_text)
            await bot.send_location(admin, location.latitude, location.longitude)
        except Exception as e:
            logging.error(f"Adminga yuborishda xatolik: {e}")

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Zakaz qilishni boshlash")
    await message.answer("Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz. Rahmat!", reply_markup=kb)
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "✏️ O‘zgartirish", state=OrderState.confirming)
async def edit_order(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in products:
        kb.add(cat)
    kb.add("❌ Buyurtmani bekor qilish")
    await message.answer("Buyurtmani qayta tanlang:", reply_markup=kb)
    user_cart[message.from_user.id] = []
    await OrderState.choosing_product.set()

@dp.message_handler(lambda msg: msg.text in ["❌ Bekor qilish", "❌ Buyurtmani bekor qilish"], state='*')
async def cancel_order(message: types.Message, state: FSMContext):
    await state.finish()
    user_cart.pop(message.from_user.id, None)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Zakaz qilishni boshlash")
    await message.answer("✅ Buyurtma bekor qilindi. Yangi buyurtma berish uchun 'Zakaz qilishni boshlash' tugmasini bosing.", reply_markup=kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
