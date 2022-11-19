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
    mycursor.execute(f"SELECT teleid FROM students WHERE teleid = %s",(message.chat.id,))
    result = mycursor.fetchone()
    if not result:
        mycursor.execute(f"SELECT teleid FROM curators WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        if not result:
            service = telebot.types.ReplyKeyboardMarkup(True, True)
            service.row('student', 'curator')
            service.row('teacher')
            user_name = message.from_user.username
            bot.send_message(message.chat.id, f"Привет, {user_name}! Это NIS Assistant чат бот. \n Выберите свою роль".format(message.from_user), reply_markup = service)
        elif message.chat.id == result[0]:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Отправить сообщение')
            msg = bot.send_message(message.chat.id, f'Куратор {message.from_user.firs_name}', reply_markup = service)
            bot.register_next_step_handler(msg, curator_main)

@bot.message_handler(content_types=["text", "photo"])
def bot_message(message):
    if message.text == 'student':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('/menu')
        msg = bot.send_message(message.chat.id, 'Введите email', reply_markup=service)
        bot.register_next_step_handler(msg, check_student)
    if message.text == 'curator':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('/menu')
        msg = bot.send_message(message.chat.id, 'Введите email', reply_markup=service)
        bot.register_next_step_handler(msg, check_curator)

def check_student(message):
    global semail
    semail = message.text.lower()
    mycursor.execute(f"SELECT email FROM students WHERE email = %s",(semail,))
    result = mycursor.fetchone()
    if result:
        mycursor.execute(f"SELECT teleid FROM students WHERE email = %s",(semail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
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

def check_curator(message):
    global cemail
    cemail = message.text.lower()
    mycursor.execute(f"SELECT email FROM curators WHERE email = %s",(cemail,))
    result = mycursor.fetchone()
    if result:
        mycursor.execute(f"SELECT teleid FROM curators WHERE email = %s",(cemail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Отправить сообщение')
            msg = bot.send_message(message.chat.id, f'Куратор {message.from_user.firs_name}', reply_markup = service)
            bot.register_next_step_handler(msg, curator_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass_curator)
        else:
            msg = bot.send_message(message.chat.id, 'В доступе отказано')
            bot.register_next_step_handler(msg, start)
    else:
        msg = bot.send_message(message.chat.id, 'Куратор с таким email не найден')
        bot.register_next_step_handler(msg, start)

def check_pass(message):
        mycursor.execute(f"SELECT pass FROM students WHERE email = %s",(semail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE students SET teleid = {message.chat.id} WHERE email = %s",(semail,))
            mydb.commit()
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Расписание', 'Мероприятия')
            service.row('Кружки')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, student_main)
        else:
            msg = bot.send_message(message.chat.id, 'Не правильный пароль')
            bot.register_next_step_handler(msg, start)

def check_pass_curator(message):
        mycursor.execute(f"SELECT pass FROM curators WHERE email = %s",(cemail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE curators SET teleid = {message.chat.id} WHERE email = %s",(cemail,))
            mydb.commit()
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Отправить сообщение')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, curator_main)
        else:
            msg = bot.send_message(message.chat.id, 'Не правильный пароль')
            bot.register_next_step_handler(msg, start)

def student_main(message):
    if message.text == 'Расписание':
        mycursor.execute(f"SELECT class FROM students WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        img = 'sources/'+result[0]+'.png'
        bot.send_photo(message.chat.id, photo=open(img, 'rb'))

def curator_main(message):
    if message.text == 'Отправить сообщение':
        mycursor.execute(f"SELECT shanyrak FROM curators WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        mycursor.execute(f"SELECT class1, class2, class3 FROM shanyraks WHERE name = %s",(result[0],))
        classes = mycursor.fetchall()
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        for row in classes[0]:
            service.row(row)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Выберите класс', reply_markup = service)
        bot.register_next_step_handler(msg, start)

def select_class(message):
    if message.text == 'Выбор классов отменен':
        msg = bot.send_message(message.chat.id, 'Отправка сообщения отменена')
        bot.register_next_step_handler(msg, start)
    else:
        global students
        mycursor.execute(f"SELECT teleid FROM sudents WHERE class = %s",(message.text))
        students = mycursor.fetchall()
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Напишите им сообщение или отправьте картинку', reply_markup = service)
        bot.register_next_step_handler(msg, event)

def event(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Отправка сообщения отменена')
        bot.register_next_step_handler(msg, start)
    if message.text == 'Да':
        msg = bot.send_message(message.chat.id, 'Напишите им сообщение', reply_markup = service)
        bot.register_next_step_handler(msg, event)
    elif message.content_type == "photo":
        raw = message.photo[2].file_id
        name = raw+".jpg"
        file_info = bot.get_file(raw)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(name,'wb') as new_file:
            new_file.write(downloaded_file)
        img = open(name, 'rb')
        for student in students[0]:
            bot.send_photo(student, img)
        bot.send_message(message.chat.id, 'Картинки успешно отправлены')
        msg = bot.send_message(message.chat.id, 'Желаете также отправить сообщение? (Да/Отмена)')
        bot.register_next_step_handler(msg, event)
    else:
        for student in students[0]:
            bot.send_message(student, message.text)
        msg = bot.send_message(message.chat.id, 'Сообщение успешно отправлено')
        bot.register_next_step_handler(msg, start)


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
