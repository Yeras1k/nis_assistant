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
    mycursor.execute(f"SELECT teleid FROM teachers WHERE teleid = %s",(message.chat.id,))
    result = mycursor.fetchone()
    if result[0] == message.chat.id:
        service = telebot.types.ReplyKeyboardMarkup(True, False)
        service.row('Урок')
        global tsubject
        mycursor.execute(f"SELECT subject FROM teachers WHERE teleid = %s",(message.chat.id,))
        tsubject = mycursor.fetchone()
        msg = bot.send_message(message.chat.id, f'Учитель {message.from_user.first_name}', reply_markup = service)
        bot.register_next_step_handler(msg, teacher_main)
    else:
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('student', 'curator')
        service.row('teacher', 'parent')
        user_name = message.from_user.username
        bot.send_message(message.chat.id, f"Привет, {user_name}! Это NIS Assistant чат бот. \n Выберите свою роль".format(message.from_user), reply_markup = service)


@bot.message_handler(content_types=["text", "photo"])
def bot_message(message):
    if message.text == 'student':
        msg = bot.send_message(message.chat.id, 'Введите email')
        bot.register_next_step_handler(msg, check_student)
    if message.text == 'curator':
        msg = bot.send_message(message.chat.id, 'Введите email')
        bot.register_next_step_handler(msg, check_curator)
    if message.text == 'teacher':
        msg = bot.send_message(message.chat.id, 'Введите email')
        bot.register_next_step_handler(msg, check_teacher)

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
            msg = bot.send_message(message.chat.id, f'Куратор {message.from_user.first_name}', reply_markup = service)
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

def check_teacher(message):
    global temail
    temail = message.text.lower()
    mycursor.execute(f"SELECT email FROM teachers WHERE email = %s",(temail,))
    result = mycursor.fetchone()
    if result:
        mycursor.execute(f"SELECT teleid FROM teachers WHERE email = %s",(temail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Урок')
            global tsubject
            mycursor.execute(f"SELECT subject FROM teachers WHERE teleid = %s",(message.chat.id,))
            tsubject = mycursor.fetchone()
            msg = bot.send_message(message.chat.id, f'Учитель {message.from_user.first_name}', reply_markup = service)
            bot.register_next_step_handler(msg, teacher_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass_teacher)
        else:
            msg = bot.send_message(message.chat.id, 'В доступе отказано')
            bot.register_next_step_handler(msg, start)
    else:
        msg = bot.send_message(message.chat.id, 'Учитель с таким email не найден')
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

def check_pass_teacher(message):
        mycursor.execute(f"SELECT pass FROM teachers WHERE email = %s",(temail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE teachers SET teleid = {message.chat.id} WHERE email = %s",(temail,))
            mydb.commit()
            global tsubject
            mycursor.execute(f"SELECT subject FROM teachers WHERE teleid = %s",(message.chat.id,))
            tsubject = mycursor.fetchone()
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Урок')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, teacher_main)
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
        bot.register_next_step_handler(msg, select_class)

def teacher_main(message):
    if message.text == 'Урок':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Напишите класс и подгруппу(через пробел) в котором сейчас ведете урок', reply_markup = service)
        bot.register_next_step_handler(msg, teacher_class)

def teacher_class(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Выбор ученика отменен')
        bot.register_next_step_handler(msg, start)
    else:
        global group
        group = message.text
        gr = group.split()
        if len(gr) == 2:
            mycursor.execute(f"SELECT id, name, surname FROM students WHERE class = %s AND subgroup = %s",(gr[0], gr[1],))
            studentss = mycursor.fetchall()
        elif len(gr) == 1:
            mycursor.execute(f"SELECT id, name, surname FROM students WHERE class = %s",(gr[0],))
            studentss = mycursor.fetchall()
        reply_message = "- All class:\n"
        for i in range(len(studentss)):
            reply_message += f"{studentss[i][0]}: {studentss[i][1]} {studentss[i][2]}"
        bot.send_message(message.chat.id, reply_message)
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, "Введите id ученика которым хотите написать комментарий", reply_markup = service)
        bot.register_next_step_handler(msg, select_student)

def select_student(message):
    if message.text == group:
        bot.send_message(message.chat.id, 'Выбор ученика отменен')
        teacher_class(message.text)
    elif message.text.isdigit():
        global com_student
        com_student = message.text
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, "Напишите свой комментарий", reply_markup = service)
        bot.register_next_step_handler(msg, give_comment)
    else:
        bot.send_message(message.chat.id, 'Ошибка')
        teacher_class(group)

def give_comment(message):
    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Написание комментария отменено')
        teacher_class(group)
    else:
        mycursor.execute(f"SELECT teleid, name, surname FROM students WHERE id = %s",(com_student,))
        result = mycursor.fetchmany(1)
        mycursor.execute(f"INSERT INTO warns(teleid, name, surname, comment, subject) VALUES(%s, %s, %s, %s, %s)", (result[0][0], result[0][1], result[0][2], message.text, tsubject[0]))
        mydb.commit()
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row(group)
        msg = bot.send_message(message.chat.id, "Комментарий сохранен", reply_markup = service)
        bot.register_next_step_handler(msg, teacher_class) 

def select_class(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Отправка сообщения отменена')
        bot.register_next_step_handler(msg, start)
    else:
        global students
        mycursor.execute(f"SELECT teleid FROM students WHERE class = %s",(message.text,))
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
        msg = bot.send_message(message.chat.id, 'Напишите им сообщение или отправьте картинку')
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
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Да','Отмена')
        msg = bot.send_message(message.chat.id, 'Желаете еще что нибудь отправить? (Да/Отмена)', reply_markup = service)
        bot.register_next_step_handler(msg, event)
    else:
        for student in students[0]:
            bot.send_message(student, message.text)
        bot.send_message(message.chat.id, 'Сообщение успешно отправлено')
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Да','Отмена')
        msg = bot.send_message(message.chat.id, 'Желаете еще что нибудь отправить? (Да/Отмена)', reply_markup = service)
        bot.register_next_step_handler(msg, event)


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
