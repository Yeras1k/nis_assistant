import os
import telebot
import logging
import random
import mysql.connector
from config import *
from flask import Flask, request

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

mydb = mysql.connector.connect(
    host = os.environ.get('MYSQLHOST'),
    port = os.environ.get('MYSQLPORT'),
    user = os.environ.get('MYSQLUSER'),
    password = os.environ.get('MYSQLPASSWORD'),
    database = os.environ.get('MYSQLDATABASE')
)
mycursor = mydb.cursor(buffered=True)

@bot.message_handler(commands=["start"])
def start(message):
    service = telebot.types.ReplyKeyboardMarkup(True, True)
    service.row('student', 'curator')
    service.row('teacher')
    user_name = message.from_user.username
    bot.send_message(message.chat.id, f"Привет, {user_name}! Это NIS Assistant чат бот. \n Выберите свою роль".format(message.from_user), reply_markup = service)

@bot.message_handler(content_types=["text"])
def bot_message(message):
    if message.text == 'student':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('/menu')
        msg = bot.send_message(message.chat.id, 'Введите email', reply_markup=service)
        bot.register_next_step_handler(msg, check_student)

def check_student(message):
    global semail
    semail = message.text.lower()
    mycursor.execute(f"SELECT email FROM students WHERE email = %s",(semail,))
    result = mycursor.fetchone()
    if result:
        mycursor.execute(f"SELECT teleid FROM students WHERE email = %s",(semail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, True)
            service.row('Расписание', 'Мероприятия')
            service.row('Кружки')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, student_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass)
        else:
            msg = bot.send_message(message.chat.id, 'В доступе отказано')
            bot.register_next_step_handler(msg, start)
    else:
        msg = bot.send_message(message.chat.id, 'Ученик с таким email не найден')
        bot.register_next_step_handler(msg, start)

def check_pass(message):
        mycursor.execute(f"SELECT pass FROM students WHERE email = %s",(semail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE students SET teleid = {message.chat.id} WHERE email = %s",(semail,))
            mydb.commit()
            service = telebot.types.ReplyKeyboardMarkup(True, True)
            service.row('Расписание', 'Мероприятия')
            service.row('Кружки')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
        else:
            msg = bot.send_message(message.chat.id, 'Не правильный пароль')
            bot.register_next_step_handler(msg, start)

def student_main(message):
    if message.text == 'Расписание':
        mycursor.execute(f"SELECT class FROM students WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        img = 'sources/'+result[0]+'.png'
        bot.send_photo(message.chat.id, photo=open(img, 'rb'))


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
