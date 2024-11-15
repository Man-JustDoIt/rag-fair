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
# todo      5.4 Вернуть дату и время последнего входа и текущий уровень доступа
# todo  6. Покрыть тестами вход пользователя: новый, существующий, без прав, с правами, с ограничениями

# todo  7. Только админам показывать кнопку "Добавить информацию"
# todo  8. Научиться строить сайты в зависимости от полученных данных иб БД


import asyncio
import logging
import json
import os
import sys
from dotenv import load_dotenv
import pandas as pd


from aiogram import Bot, Dispatcher, types, F
from aiogram.enums.content_type import ContentType
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode

from mquery import mquery


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

def add2log(tg_id, event, comments):

    check_ev = mquery('check_event', [event])
    if isinstance(check_ev, pd.DataFrame) and check_ev.empty:
        print(f'{BC.FAIL}Error:{BC.ENDC} В словаре событий отсутствует событие {BC.WARNING}{event}{BC.ENDC}!')
        return False
    if not mquery('add2log', [tg_id, comments, event]):
        print(f'{BC.FAIL}Error:{BC.ENDC} Не удалось добавить данные в лог {BC.WARNING}{event}{BC.ENDC} БД!')
        return False
    return True


def check_users(message: types.Message, event):
    tg_login = message.from_user.username
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    role = 'user'
    last_time = '2000-01-01'

    res = mquery('check_user_and_role', [tg_id])
    if isinstance(res, pd.DataFrame) and res.empty:
        params = [tg_id, tg_login, first_name, last_name]
        cnt = mquery('add_new_user', params)
        if not cnt:
            print(f'{BC.FAIL}Error:{BC.ENDC} Не удалось добавить пользователя {first_name or tg_login} в БД!')
            return False
        else:
            print(f'{BC.OKBLUE}В БД добавлено {cnt} записей.{BC.ENDC}')
        new_user = 1
    elif isinstance(res, pd.DataFrame):
        new_user = 0
        role = res['role'].iloc(0)[0] if res['role'].iloc(0)[0] is not None else role
        res = mquery('last_event_time', [tg_id, event])
        if isinstance(res, pd.DataFrame) and not res.empty:
            last_time = res['report_dt'].iloc(0)[0] if res['report_dt'].iloc(0)[0] is not None else last_time
    else:
        return False

    if new_user == 1:
        msg = f'Добро пожаловать {first_name}!'
        comments = f'{tg_login}: {role} - регистрация нового пользователя.'
    else:
        msg = f'Привет {first_name}!'
        comments = f'{tg_login}: {role} - вход зарегистрированного пользователя'
        comments += f", предыдущий вход {last_time} " if last_time != '2000-01-01' else '.'

    return msg if add2log(tg_id, event, comments) else False

# обработка команды /start от бота
@dp.message(CommandStart())
async def start(message: types.Message):
    msg = check_users(message, 'команда /start')
    text = 'Что-то пошло не так!' if not msg else msg
    await message.answer(text=text, reply_markup=create_btn())


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

    if not mquery('create_tables'):
        print(f'{BC.FAIL}Error: не удалось проверить целостность таблиц БД!{BC.ENDC}')
    else:
        asyncio.run(main())
