#       0. Скрыть токен бота
#       1. Клавиша старт и помощь внизу бота и на главном меню
#       2. Приветствие с ФИО
#       3. Вывести информацию при нажатии кнопки "О проекте"
#       4. Добавить БД - SQLight, создать таблицы, если необходимо
#       5. Добавить в лог БД факт входа пользователя
#           5.1 Проверить наличие пользователя в БД. Если нет, то записать
#           5.1.1 Обеспечить хранение нескольких SQL скриптов в одном файле
#           5.2 Записать в лог исполнения команды /start
#           5.3 Добавить витрину с полномочиями: admin, content_redactor, banned_user
#           5.4 Вернуть дату и время последнего входа и текущий уровень доступа
#   6. Покрыть тестами вход пользователя: новый, существующий, без прав, с правами, с ограничениями

# todo  7. Доработки:
# todo      7.0 Объединить "Открыть приложение" и команду /start
# todo      7.1 Изменить текст "О проекте" на что-то более воодушевлющее

# todo  8. Создать ЛК пользователя:
# todo      8.0 Создать welcome page для незарегистрированных пользователей с переходом в ЛК
# todo      8.1 Изменить текcт welcome page, если banned user
# todo      8.2 Создать страницу ЛК для user
# todo          8.2.1    Создать форму для ввода данных
# todo          8.2.1.1    Проверить корректность ввода сотового номера, возможно выбор страны из списка с лидером РФ
# todo          8.2.1.2    Выбрать из списка страну присутствия, лидер РФ
# todo          8.2.1.3    Выбрать из списка ТБ, если не РФ, то РБ или Индия
# todo          8.2.1.4    Найти и использовать список городов РФ, предусмотреть "город не найден"
# todo          8.2.1.5    ??? Может ли пользователь разрешить передавать нам геоданные?
# todo          8.2.1.6    Реализовать с помощью ре простую проверку email
# todo          8.2.1.6    Прочитать ФЗ по этому поводу обработки персональных данных
# todo          8.2.1.7    Подготовить форму с текстом согласия на обработку и хранение персональных данных
# todo          8.2.1.8    Подготовить форму с драфтом правил
# todo      8.3 Создать тестовую основную страницу с иконкой ЛК
# todo      8.4 Если пользователь зарегистрирован - переходим на основную страницу




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
