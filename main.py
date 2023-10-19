from tasks import simple_task

token = '5825452986:AAHgnNtNCx1tQNIMsVowyQcJuYce71MDbvo'

import csv
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Создаем экземпляры бота диспетчера
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer(
        f'Привет, {message.from_user.username}👋🏻\n\n' + 'Я могу помочь найти тебе фильм по твоему описанию! Для этого отправь то, что ты хочешь увидеть, а я постараюсь подобрать что-нибудь подходящее!🎬🍿')


@dp.message_handler()
async def handle_answer(message: types.Message):
    # Получаем ответ пользователя
    answer = message.text

    # # Открываем файл CSV для записи
    # with open('answers.csv', 'a', newline='') as file:
    #     writer = csv.writer(file)

    #     # Записываем ответ в файл
    #     writer.writerow([message.from_user.id, answer])
    simple_task.apply_async([token, message.from_user.id, message.text], queue='main_queue')
    await message.reply("Спасибо за ответ! Ваш запрос обрабатывается, пожалуйста, ожидайте!")


if __name__ == '__main__':
    executor.start_polling(dp)
