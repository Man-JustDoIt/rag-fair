from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.web_app_info import WebAppInfo

bot = Bot('8007893303:AAEBlTEpJ96g2MAEJr_zy83IXP8H9mYs3do')
dp = Dispatcher(bot)
url = 'https://www.google.com/'


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('Открыть веб сраницу', web_app=WebAppInfo(url=url)))
    await message.answer('Добро пожаловать на канал профсоюза Сбербанка', reply_markup=markup)

executor.start_polling(dp)
