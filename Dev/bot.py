# todo  0. Скрыть токен бота    -   done
# todo  1. Клавиша старт и помощь внизу бота и на главном меню  -   done
# todo  2. Приветствие с ФИО    -   done
# todo  3. Вывести информацию при нажатии кнопки "О проекте"    -   done
# todo  4. Добавить БД - SQLight, создать таблицы, если необходимо  -   done
# todo  5. Добавить в лог БД факт входа пользователя
# todo      5.1 Проверить наличие пользователя в БД. Если нет, то записать  -   done
# todo      5.1.1 Обеспечить хранение нескольких SQL скриптов в одном файле  -   done
# todo      5.2 Записать в лог исполнения команды /start  -   done
# todo      5.3 Добавить витрину с полномочиями: admin, content_redactor, banned_user  -   done
# todo      5.4 Вернуть дату и время последнего входа и текущий уровень доступа - done
# todo  6. Покрыть тестами вход пользователя: новый, существующий, без прав, с правами, с ограничениями

# todo  7. Только админам показывать кнопку "Добавить информацию"
# todo  8. Научиться строить сайты в зависимости от полученных данных иб БД


import asyncio
import logging
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd


from aiogram import Bot, Dispatcher, types, F
from aiogram.enums.content_type import ContentType
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode

from mquery import mquery
import muser as mu


class BC:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


logging.basicConfig(level=logging.INFO)
load_dotenv()
bot = Bot(os.getenv('bot_token'))

url = "https://man-justdoit.github.io/rag-fair/index.html"
dp = Dispatcher()


def check_users_and_log(message: types.Message, event_name):
    user = {'tg_login': message.from_user.username, 'tg_id': message.from_user.id,
            'first_name': message.from_user.first_name, 'last_name': message.from_user.last_name}

    # Проверяем наличие пользователя в БД
    user_dict = mu.add_or_update_user(**user)
    if not user_dict:
        return False
    # Записываем в БД в событие
    event_dict = mu.add_event2log(tg_id=user['tg_id'], event_name=event_name)
    if not event_dict:
        return False

    return_dict = {key: val for key, val in event_dict.items() if key in ('report_dt', 'last_event_dt', 'event_name')}
    return_dict.update(user_dict)
    return return_dict


# обработка команды /start от бота
@dp.message(CommandStart())
async def start(message: types.Message):
    event_dict = check_users_and_log(message, '/start')
    if not event_dict:
        msg = 'Что-то пошло не так!'
    elif event_dict['last_event_dt'] == '2000-01-01 00:00:00':
        msg = 'Добро пожаловать, '
    else:
        msg = 'Привет, '
    msg += event_dict['first_name'] or event_dict['tg_login']
    msg += '!'

    await message.answer(text=msg, reply_markup=create_btn())


# обработка команды /help от бота
@dp.message(lambda message: message.text in ['/help', "О проекте"])
async def process_start_command(message: types.Message) -> None:
    msg = ('Приложение \n'
           '1. Информирует о программе лояльности профсоюзной организации Сбера \n' 
           '2. Дает возможность размещать собственные частные объявления')
    await message.answer(msg)


@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def parse_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    print(data)
    await message.answer(f'<b>{data["title"]}</b>\n\n<code>{data["desc"]}</code>\n\n{data["text"]}',
                         parse_mode=ParseMode.HTML)

def create_btn():
    # Инициализируем ссылку на сайт
    webAppInfo = types.WebAppInfo(url=url)
    kb = [
            [
                types.KeyboardButton(text="Открыть приложение", web_app=webAppInfo),
                types.KeyboardButton(text="О проекте")
            ],
         ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберете действие"
    )
    return keyboard


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":

    # if not mquery('create_tables'):
    #     print(f'{BC.FAIL}Error: не удалось проверить целостность таблиц БД!{BC.ENDC}')
    # else:
    asyncio.run(main())
