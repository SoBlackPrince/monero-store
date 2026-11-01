import os
import json
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client
import asyncio
import urllib.parse

BOT_TOKEN = "9018579736:AAFbUfg0YIRZnWGlEBAfw8qUC1w1xuuXbN4"
SUPABASE_URL = "https://uhchxpzsnjcjddggqosh.supabase.co"
SUPABASE_KEY = "sb_publishable_KtMIJ4h3tDuEF_p4c_7VIg_iViLfBQf"
TELEGRAM_USERNAME = "BestMonero"
SITE_URL = "https://monero-store.vercel.app"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="🛒 Наличие аккаунтов", callback_data="accounts")],
        [InlineKeyboardButton(text="⭐ Купить звезды", callback_data="stars_menu")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="🌐 Наш сайт", url=SITE_URL)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_back_menu():
    kb = [[InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в **Monero Store**!\n\n"
        "Здесь вы можете посмотреть наличие аккаунтов, купить звезды или прочитать инструкцию.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "main_menu")
async def process_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню **Monero Store**\nВыберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "instruction")
async def process_instruction(callback: types.CallbackQuery):
    text = (
        "📖 **Инструкция по покупке аккаунтов:**\n\n"
        "Сайт не имеет функции оплаты аккаунтов прямо на нем, для оплаты телеграмм аккаунтов вы должны написать мне в личные сообщения и сказать какой аккаунт вы хотите купить.\n\n"
        "**Оплата может происходить:**\n"
        "• Рублями\n"
        "• USDT\n"
        "• Телеграмм звездами\n\n"
        "При получении аккаунта заходить с впном данной страны, которой вы купили аккаунт. Советую вам отлежаться пару дней и не трогать его, чтоб телеграмм не выдал вам спамблок, за спамблок я не ручаюсь.\n\n"
        "Приятных покупок!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "accounts")
async def process_accounts(callback: types.CallbackQuery):
    await callback.answer("Загружаю товары...")
    try:
        response = supabase.table('products').select('*').gt('qty', 0).execute()
        products = response.data
    except Exception as e:
        await callback.message.edit_text("❌ Ошибка загрузки товаров.", reply_markup=get_back_menu())
        return

    if not products:
        await callback.message.edit_text("😔 Товаров в наличии нет.", reply_markup=get_back_menu())
        return

    await callback.message.edit_text("🛒 **Аккаунты в наличии:**", parse_mode="Markdown")

    for p in products:
        text = f"✈️ **{p['flag']} {p['country']} {p['code']}**\n\n📝 {p['short_desc']}\n💰 Цена: {p['price']}\n📦 В наличии: {p['qty']} шт."
        msg = f"Привет! Хочу купить аккаунт {p['flag']} {p['country']} {p['code']}.\nСсылка на товар: {SITE_URL}/?item={p['id']}"
        buy_url = f"https://t.me/{TELEGRAM_USERNAME}?text={urllib.parse.quote(msg)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛍 Купить", url=buy_url)]])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")

    await callback.message.answer("Выберите действие:", reply_markup=get_back_menu())

STARS_PRICE = 1.5

@dp.callback_query(lambda c: c.data == "stars_menu")
async def process_stars_menu(callback: types.CallbackQuery):
    text = f"⭐ **Курс Monero Store**\n1.5 RUB = 1 Звезда\n\nВыберите количество звезд:"
    kb = []
    for amount in [50, 100, 200, 300, 400, 500, 1000]:
        kb.append([InlineKeyboardButton(text=f"{amount} звезд", callback_data=f"buy_stars_{amount}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("buy_stars_"))
async def process_buy_stars(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[2])
    price = amount * STARS_PRICE
    text = f"Отлично! С вас **{price} рублей** за {amount} звезд.\n\nНажмите кнопку ниже, чтобы связаться с продавцом:"
    msg = f"Привет! Хочу купить у тебя {amount} звезд!"
    buy_url = f"https://t.me/{TELEGRAM_USERNAME}?text={urllib.parse.quote(msg)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Написать продавцу", url=buy_url)], [InlineKeyboardButton(text="⬅️ Назад", callback_data="stars_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update = types.Update.model_validate(json.loads(post_data.decode('utf-8')), context={"bot": bot})
        
        async def process():
            await dp.feed_update(bot, update)
            
        asyncio.run(process())
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")