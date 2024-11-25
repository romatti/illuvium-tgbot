import const
import config
import requests
import asyncio
import logging
import sys
import datetime
import json

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

import aiosqlite

TOKEN = config.TOKEN
dp = Dispatcher()


# Билдер клавиатуры
def webapp_builder():
    builder = InlineKeyboardBuilder()
    builder.button(text="View collections", web_app=WebAppInfo(url="https://romatti.github.io/illuvium-tgbot/"))
    return builder.as_markup()


# Добавить пользователя в базу при нажатии старт
async def add_to_database(telegram_id, username, wallet=""):
    async with aiosqlite.connect('illuvium-tgbot.db') as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users "
                         "(telegram_id BIGINT, username TEXT, date TEXT, wallet TEXT, number_of_requests BIGINT)")
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        data = await cursor.fetchone()
        print(data)
        if data is None:
            # создаем в первый раз
            date = f'{datetime.date.today()}'
            await db.execute("INSERT INTO users (telegram_id, username, date, wallet, number_of_requests) "
                             "VALUES (?,?,?,?,?) ",
                             (telegram_id, username, date, wallet, 0))
            await db.commit()
        else:
            if wallet != "":
                await db.execute("UPDATE users SET wallet = ? WHERE telegram_id = ?",
                                 (wallet, telegram_id))
                await db.commit()


def collection_parsing(address):
    collection = []  # Список для хранения всех данных
    url = f"https://api.immutable.com/v1/assets?user={address}&collection=0x205634b541080afff3bbfe02dcc89f8fa8a1f1d4"
    headers = {'Accept': "application/json"}
    params = {'cursor': ''}
    while True:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка: {response.status_code}")
            break
        json_response = response.json()  # <class 'dict'>
        collection.extend(json_response.get('result', []))
        if json_response.get('remaining', 0) == 0:
            break
        cursor = json_response.get('cursor')
        if not cursor:
            print("Курсор не найден.")
            break
        params.update({'cursor': cursor})

    return collection


def collection_processing(collection):
    illuvium_collection = {}
    print(len(collection))
    for element in collection:
        if element['collection']['name'] == 'Illuvium Illuvials':
            name = element['name'] + ' ' + element['metadata']['Finish']
            if illuvium_collection.get(name) is None:
                illuvium_collection[name] = 1
            else:
                illuvium_collection[name] = illuvium_collection[name] + 1
    print(illuvium_collection)
    return illuvium_collection


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! To view statistics, enter your IMX wallet Address..")
    await add_to_database(message.from_user.id, message.from_user.username)


@dp.message(F.text.lower().startswith == '0x' and F.text.len() == 42)
async def add_wallet(message: Message) -> None:
    try:
        await add_to_database(message.from_user.id, message.from_user.username, message.text)
        await message.answer("Success! Please wait while the collection is loading (~ 30 sec)..")
        collection = collection_parsing(message.text)
        if len(collection) > 0:
            illuvium_collection = collection_processing(collection)
            await message.answer(str(len(illuvium_collection)))
            await message.answer("Success! To view collections press the button below!", reply_markup=webapp_builder())
        else:
            await message.answer("Collection is empty")
    except TypeError:
        await message.answer("Error!")


@dp.message()
async def echo_handler(message: Message) -> None:
    await message.answer("To view statistics, enter your IMX wallet Address (0x..)..")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
