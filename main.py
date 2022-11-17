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
mycursor = mydb.cursor()

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
        msg = bot.send_message(message.from_user.id, 'Введите email', reply_markup=service)
        bot.register_next_step_handler(msg, check_student)

def check_student(message):
    semail = message.text.lower()
    mycursor.execute(f"SELECT email FROM students WHERE email = `{semail}`")
    result = mycursor.fetchall()
    bot.send_message(message.chat.id, f'{result[0]}')



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
