# todo  0. Скрыть токен бота    -   done
# todo  1. Клавиша старт внизу бота
# todo  2. Приветствие с ФИО
# todo  3. Переход на страницу с выбором


import asyncio
import logging
import json
import os
from dotenv import load_dotenv


from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums.content_type import ContentType
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode


logging.basicConfig(level=logging.INFO)
load_dotenv()
bot = Bot(os.getenv('bot_token'))

url = "https://man-justdoit.github.io/rag-fair/index.html"
dp = Dispatcher()


# вызов функции /start
@dp.message(CommandStart())
async def start(message: types.Message):
    webAppInfo = types.WebAppInfo(url=url)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Запустить приложение', web_app=webAppInfo, resize_keyboard=True))

    await message.answer(text='Привет!', reply_markup=builder.as_markup())


@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def parse_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    print(data)
    await message.answer(f'<b>{data["title"]}</b>\n\n<code>{data["desc"]}</code>\n\n{data["text"]}',
                         parse_mode=ParseMode.HTML)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())