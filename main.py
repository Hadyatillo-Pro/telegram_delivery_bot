import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from math import ceil
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token="8333566979:AAGMy0P_97W-m-twcIy-mm6bm1q78zY0Kcw")
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
    waiting_for_day = State()
    waiting_for_hour = State()
    
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
    
@dp.message_handler(state=OrderState.sending_contact, content_types=types.ContentType.CONTACT)
async def after_phone_handler(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number
    await state.update_data(contact=contact)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Bugunga", "Ertaga", "2 kundan keyinga")

    await message.answer("📅 Buyurtmangizni qachonga yetkazib berishimizni hohlaysiz?", reply_markup=markup)
    await OrderState.waiting_for_day.set()
    
@dp.message_handler(state=OrderState.waiting_for_day)
async def handle_day_choice(message: types.Message, state: FSMContext):
    await state.update_data(delivery_day=message.text)

    times = ["8:00", "8:30", "9:00", "9:30", "10:00", "10:30", "11:00", "11:30",
             "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
             "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30"]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    for i in range(0, len(times), 3):
        markup.add(*times[i:i+3])

    await message.answer("🕒 Qaysi soatga yetkazib beraylik?", reply_markup=markup)
    await OrderState.waiting_for_hour.set()

@dp.message_handler(state=OrderState.confirming)
async def handle_confirmation(message: types.Message, state: FSMContext):
    if message.text == "✅ Tasdiqlash":
        data = await state.get_data()
        cart = user_cart.get(message.from_user.id, [])
        order_text = "\n".join([f"{p} x {q}" for p, q in cart])
        total = sum(
            products[cat][prod] * qty
            for prod, qty in cart
            for cat in products
            if prod in products[cat]
        )
    order_text = "\n".join([f"{p} x {q}" for p, q in cart])
    total = sum(products[cat][prod] * qty for prod, qty in cart for cat in products if prod in products[cat])

admin_text = (
    f"📥 Yangi buyurtma:\n\n"
    f"🛍 {order_text}\n"
    f"💰 To‘lov: {data.get('payment_method')}\n"
    f"📞 Telefon: {data.get('phone')}\n"
    f"📍 Lokatsiya: {data.get('location')}\n"
    f"📅 Yetkazish: {data.get('delivery_day')} soat {data.get('delivery_hour')}\n"
    f"💵 Umumiy: {total} so‘m"
)

for admin_id in ADMIN_IDS:
    await bot.send_message(admin_id, admin_text)

    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz. Rahmat!", reply_markup=ReplyKeyboardRemove())
    user_cart[message.from_user.id] = []
    await state.finish()

if message.text == "✏️ O‘zgartirish":
    await message.answer("Buyurtmani boshidan boshlash uchun /start ni bosing.", reply_markup=ReplyKeyboardRemove())
    user_cart[message.from_user.id] = []
    await state.finish()

elif message.text == "❌ Bekor qilish":
     await message.answer("Buyurtma bekor qilindi. /start orqali yangidan boshlang.", reply_markup=ReplyKeyboardRemove())
     user_cart[message.from_user.id] = []
     await state.finish()

else:
    await message.answer("Iltimos, quyidagilardan birini tanlang: ✅ Tasdiqlash, ✏️ O‘zgartirish, ❌ Bekor qilish.")

for admin in ADMINS:
    try:
        await bot.send_message(admin, full_text)
        await bot.send_location(admin, location.latitude, location.longitude)
try:
    # bu yerda xatolik bo'lishi mumkin bo'lgan kod
    phone = data['phone']
    
except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")

kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add("Zakaz qilishni boshlash")
await message.answer("Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz. Rahmat!,Agar Qandaydur takliflar bo'lsa marhamat:@Hadyatillo25 ga murojaat qilishingiz mumkin!", reply_markup=kb)
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

@dp.message_handler(lambda message: message.text, state='*')
async def block_ads_handler(message: types.Message, state: FSMContext):
    text = message.text.lower()
    blocklist = ["http://", "https://", "t.me/", "airdrop", "claim", "bonus", "refer", "get free", "join now", "free crypto"]

    if any(bad in text for bad in blocklist):
        await message.delete()
        try:
            await message.answer("❌ Reklama, havola yoki spam yuborish taqiqlangan.")
        except:
            pass
        return  # Shunda boshqa handlerlar ishlamaydi

    await dp.process_updates([types.Update(message=message)])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
