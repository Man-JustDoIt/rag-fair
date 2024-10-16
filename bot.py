# todo  0. Скрыть токен бота    -   done
# todo  1. Клавиша старт и помощь внизу бота и на главном меню    -   done
# todo  2. Приветствие с ФИО    -   done
# todo  3. Вывести информацию при нажатии кнопки "О проекте"
# todo  4. Добавить БД - SQLight
# todo  5. Добавить в лог БД факт входа пользователя
# todo  6. Проверить пользователя на админство
# todo  7. Только админам показывать кнопку "Добавить информацию"



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

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonPollType

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot = Bot(os.getenv('bot_token'))

url = "https://man-justdoit.github.io/rag-fair/index.html"
dp = Dispatcher()


# обработка команды /start от бота
@dp.message(CommandStart())
async def start(message: types.Message):
    tg_login = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    user_id = message.from_user.id
    await message.answer(text=f'Привет {first_name} !', reply_markup=create_btn())

@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def parse_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    print(data)
    await message.answer(f'<b>{data["title"]}</b>\n\n<code>{data["desc"]}</code>\n\n{data["text"]}',
                         parse_mode=ParseMode.HTML)


def create_btn():
    # Инициализируем ссылку на сайт
    webAppInfo = types.WebAppInfo(url=url)
    # Инициализируем билдер
    builder = ReplyKeyboardBuilder()

    # Создаем кнопки
    start_btn = KeyboardButton(
        text='Запустить приложение',
        web_app=webAppInfo
    )
    help_btn = KeyboardButton(
        text='О проекте ПроБот'
    )

    # Добавляем кнопки в билдер
    builder.row(start_btn, help_btn, width=1)

    # Создаем объект клавиатуры
    keyboard: ReplyKeyboardMarkup = builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
