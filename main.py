import os
import telebot
import logging
import random
from pytz import timezone
from datetime import date, datetime
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
    global almatyZone, dt_format
    almatyZone = datetime.now(timezone('Asia/Almaty'))
    dt_format = "%d.%m.%y"
    service = telebot.types.ReplyKeyboardMarkup(True, True)
    service.row('student', 'curator')
    service.row('teacher', 'parent')
    user_name = message.from_user.username
    dt_format = "%d.%m.%y %H:%M"
    msg = f"Привет, {user_name}! Это NIS Assistant чат бот. \n Выберите свою роль "
    bot.send_message(message.chat.id, msg.format(message.from_user), reply_markup = service)

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
    if message.text == 'parent':
        msg = bot.send_message(message.chat.id, 'Введите email ребенка. Если у вас их несколько\n то вы сможете добавить их позже')
        bot.register_next_step_handler(msg, check_parent)

def check_student(message):
    global semail
    semail = message.text.lower()
    mycursor.execute(f"SELECT email FROM students WHERE email = %s",(semail,))
    result = mycursor.fetchone()
    bot.send_message(message.chat.id, f'{result}')
    if result:
        mycursor.execute(f"SELECT teleid FROM students WHERE email = %s",(semail,))
        dbresult = mycursor.fetchone()
        bot.send_message(message.chat.id, f'{dbresult}')
        bot.send_message(message.chat.id, f'{message.chat.id}')
        if not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass)
        elif int(dbresult[0]) == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Расписание', 'Мероприятия')
            service.row('Кружки', 'Пароль родителя')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, student_main)
        else:
            bot.send_message(message.chat.id, 'В доступе отказано')
            start(message)
    else:
        bot.send_message(message.chat.id, 'Ученик с таким email не найден')
        start(message)

def check_parent(message):
    global pemail
    pemail = message.text.lower()
    mycursor.execute(f"SELECT child_email FROM parent WHERE child_email = %s",(pemail,))
    result = mycursor.fetchone()
    if result:
        mycursor.execute(f"SELECT teleid FROM parent WHERE child_email = %s",(pemail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Посмотреть комментарии к ребенку')
            service.row('Добавить ребенка', 'Обновить данные о себе')
            msg = bot.send_message(message.chat.id, f'Родитель {message.from_user.first_name}', reply_markup = service)
            bot.register_next_step_handler(msg, parent_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль. Ваш ребенок может его предоставить')
            bot.register_next_step_handler(msg, check_pass_parent)
        else:
            bot.send_message(message.chat.id, 'В доступе отказано')
            start(message)
    else:
        bot.send_message(message.chat.id, 'Ученик с таким email не найден')
        start(message)

def check_curator(message):
    global cemail
    cemail = message.text.lower()
    mycursor.execute(f"SELECT email FROM curators WHERE email = %s",(cemail,))
    result = mycursor.fetchone()
    bot.send_message(message.chat.id, f'{result}')
    if result:
        mycursor.execute(f"SELECT teleid FROM curators WHERE email = %s",(cemail,))
        dbresult = mycursor.fetchone()
        if dbresult[0] == message.chat.id:
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Отправить сообщение', 'Посмотреть деятельность учеников')
            msg = bot.send_message(message.chat.id, f'Куратор {message.from_user.first_name}', reply_markup = service)
            bot.register_next_step_handler(msg, curator_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass_curator)
        else:
            bot.send_message(message.chat.id, 'В доступе отказано')
            start(message)
    else:
        bot.send_message(message.chat.id, 'Куратор с таким email не найден')
        start(message)

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
            service.row('Отметить отутствующих')
            global tsubject
            mycursor.execute(f"SELECT subject FROM teachers WHERE teleid = %s",(message.chat.id,))
            tsubject = mycursor.fetchone()
            msg = bot.send_message(message.chat.id, f'Учитель {message.from_user.first_name}', reply_markup = service)
            bot.register_next_step_handler(msg, teacher_main)
        elif not dbresult[0]:
            msg = bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(msg, check_pass_teacher)
        else:
            bot.send_message(message.chat.id, 'В доступе отказано')
            start(message)
    else:
        bot.send_message(message.chat.id, 'Учитель с таким email не найден')
        start(message)

def check_pass(message):
        mycursor.execute(f"SELECT pass FROM students WHERE email = %s",(semail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE students SET teleid = {message.chat.id} WHERE email = %s",(semail,))
            mydb.commit()
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Расписание', 'Мероприятия')
            service.row('Кружки', 'Пароль родителя')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, student_main)
        else:
            bot.send_message(message.chat.id, 'Не правильный пароль')
            start(message)

def check_pass_parent(message):
    mycursor.execute(f"SELECT pass FROM parent WHERE child_email = %s",(pemail,))
    result = mycursor.fetchone()
    if message.text == result[0]:
        mycursor.execute(f"UPDATE parent SET teleid = {message.chat.id} WHERE child_email = %s",(pemail,))
        mydb.commit()
        service = telebot.types.ReplyKeyboardMarkup(True, False)
        service.row('Посмотреть комментарии к ребенку')
        service.row('Добавить ребенка', 'Обновить данные о себе')
        msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
        bot.register_next_step_handler(msg, parent_main)
    else:
        bot.send_message(message.chat.id, 'Не правильный пароль')
        start(message)

def check_pass_curator(message):
        mycursor.execute(f"SELECT pass FROM curators WHERE email = %s",(cemail,))
        result = mycursor.fetchone()
        if message.text == result[0]:
            mycursor.execute(f"UPDATE curators SET teleid = {message.chat.id} WHERE email = %s",(cemail,))
            mydb.commit()
            service = telebot.types.ReplyKeyboardMarkup(True, False)
            service.row('Отправить сообщение', 'Посмотреть деятельность учеников')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, curator_main)
        else:
            bot.send_message(message.chat.id, 'Не правильный пароль')
            start(message)

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
            service.row('Отметить отутствующих')
            msg = bot.send_message(message.chat.id, 'Успешно вошли', reply_markup = service)
            bot.register_next_step_handler(msg, teacher_main)
        else:
            bot.send_message(message.chat.id, 'Не правильный пароль')
            start(message)

def student_main(message):
    if message.text == 'Расписание':
        mycursor.execute(f"SELECT class FROM students WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        img = 'sources/'+result[0]+'.png'
        bot.send_photo(message.chat.id, photo=open(img, 'rb'))
        start(message)
    elif message.text == 'Пароль родителя':
        mycursor.execute(f"SELECT email FROM students WHERE teleid = %s",(message.chat.id,))
        semail = mycursor.fetchone()
        mycursor.execute(f"UPDATE parent SET child = {message.chat.id} WHERE child_email = %s",(semail[0],))
        mydb.commit()
        mycursor.execute(f"SELECT pass FROM parent WHERE child_email = %s",(semail[0],))
        result = mycursor.fetchone()
        password = 'Пароль для родителя: ' + result[0]
        bot.send_message(message.chat.id, password)
        start(message)
    elif message.text == 'Кружки':
        service = telebot.types.ReplyKeyboardMarkup(True, False)
        mycursor.execute(f"SELECT hobby FROM hobbys WHERE teleid = %s",(message.chat.id,))
        while True:
            result = mycursor.fetchone()
            if result:
                service.row(result[0])
            else:
                break
        service.row('Добавить кружок', 'Назад')
        msg = bot.send_message(message.chat.id, 'Выберите кружок', reply_markup = service)
        bot.register_next_step_handler(msg, select_hobby)
            
def select_hobby(message):
    if message.text == 'Назад':
        start(message)
    elif message.text == 'Добавить кружок':
        msg = bot.send_message(message.chat.id, 'Введите название кружка в который ходите в школе и внеурочное дело')
        bot.register_next_step_handler(msg, add_hobby)
    else:
        global hobby
        hobby = message.text
        service = telebot.types.ReplyKeyboardMarkup(True, False)
        service.row('Изменить расписание кружка')
        service.row('Удалить кружок')
        service.row('Кружки')
        msg = bot.send_message(message.chat.id, 'Выберите действие', reply_markup = service)
        bot.register_next_step_handler(msg, edit_hobby)

def edit_hobby(message):
    if message.text == 'Кружки':
        student_main(message)
    elif message.text == 'Удалить кружок':
        mycursor.execute(f"DELETE FROM hobbys WHERE hobby = %s AND teleid = %s",(hobby, message.chat.id,))
        mydb.commit()
        bot.send_message(message.chat.id, 'Кружок удален')
        start(message)
        
def add_hobby(message):
    mycursor.execute(f"SELECT name, surname, class FROM students WHERE teleid = %s",(message.chat.id,))
    result = mycursor.fetchone()
    mycursor.execute(f"INSERT INTO hobbys(teleid, name, surname, class, hobby) VALUES(%s, %s, %s, %s, %s)", (message.chat.id, result[0], result[1], result[2], message.text,))
    mydb.commit()
    msg = bot.send_message(message.chat.id, 'Кружок добавлен')
    start(message)

def parent_main(message):
    if message.text == 'Посмотреть комментарии к ребенку':
        mycursor.execute(f"SELECT child_email FROM parent WHERE teleid IN (%s)", (message.chat.id,))
        service = telebot.types.ReplyKeyboardMarkup(True, False)
        while True:
            result = mycursor.fetchone()
            if result:
                service.row(result[0])
            else:
                break
        service.row('Назад')
        msg = bot.send_message(message.chat.id, 'Выберите ребенка', reply_markup = service)
        bot.register_next_step_handler(msg, my_child)
    if message.text == 'Добавить ребенка':
        msg = bot.send_message(message.chat.id, 'Введите email ребенка')
        bot.register_next_step_handler(msg, check_parent)

def my_child(message):
    if message.text == 'Назад':
        start(message)
    else:
        mycursor.execute(f"SELECT child FROM parent WHERE child_email = %s",(message.text,))
        result = mycursor.fetchone()
        mycursor.execute(f"SELECT id, name, comment, subject FROM warns WHERE teleid = %s",(result[0],))
        comments = mycursor.fetchall()
        if comments == None:
            bot.send_message(message.chat.id, 'Нет комментариев')
            start(message)
        else:
            reply_message = "- Все комментарии:\n"
            for i in range(len(comments)):
                reply_message += f"{comments[i][0]}) {comments[i][1]}: {comments[i][2]} ({comments[i][3]})\n"
        bot.send_message(message.chat.id, reply_message)
        start(message)

def curator_main(message):
    if message.text == 'Отправить сообщение':
        mycursor.execute(f"SELECT shanyrak FROM curators WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        mycursor.execute(f"SELECT class1, class2, class3 FROM shanyraks WHERE name = %s",(result[0],))
        classes = mycursor.fetchall()
        bot.send_message(message.chat.id, f'{classes}')
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        for row in classes[0]:
            service.row(row)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Выберите класс', reply_markup = service)
        bot.register_next_step_handler(msg, select_class)
    elif message.text == 'Посмотреть деятельность учеников':
        mycursor.execute(f"SELECT shanyrak FROM curators WHERE teleid = %s",(message.chat.id,))
        result = mycursor.fetchone()
        mycursor.execute(f"SELECT class1, class2, class3 FROM shanyraks WHERE name = %s",(result[0],))
        classes = mycursor.fetchall()
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        for row in classes[0]:
            service.row(row)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Выберите класс', reply_markup = service)
        bot.register_next_step_handler(msg, select_class_hobby)

def select_class_hobby(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Отправка сообщения отменена')
        bot.register_next_step_handler(msg, start)
    else:
        mycursor.execute(f"SELECT teleid, name, surname, hobby FROM hobbys WHERE class = %s ORDER BY teleid DESC",(message.text,))
        children = mycursor.fetchall()
        reply_message = "- All class:\n"
        for i in range(len(children)):
            reply_message += f"•{children[i][0]} {children[i][1]} {children[i][2]}: {children[i][3]}\n"
        bot.send_message(message.chat.id, reply_message)
        start(message)
        
def teacher_main(message):
    if message.text == 'Урок':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Напишите класс и подгруппу(через пробел) в котором сейчас ведете урок', reply_markup = service)
        bot.register_next_step_handler(msg, teacher_class)
    if message.text == 'Отметить отутствующих':
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, 'Напишите класс и подгруппу(через пробел) в котором сейчас ведете урок', reply_markup = service)
        bot.register_next_step_handler(msg, teacher_class_otmetka)

def teacher_class_otmetka(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Выбор класса отменен')
        start(message)
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
            reply_message += f"{studentss[i][0]}: {studentss[i][1]} {studentss[i][2]}\n"
        bot.send_message(message.chat.id, reply_message)
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row(group)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, "Введите id ученика который отуствует\n(у вас одна попытка иначе он попадет в базу данных отсутствующих)", reply_markup = service)
        bot.register_next_step_handler(msg, select_student_otmetka)

def select_student_otmetka(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Выбор ученика отменен')
        start(message)
    elif message.text == group:
        bot.send_message(message.chat.id, 'Выбор ученика отменен')
        teacher_class(message)
    elif message.text.isdigit():
        global com_student
        com_student = message.text
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row(group)
        mycursor.execute(f"SELECT id, name, surname, fathername, email, class FROM students WHERE id = %s",(message.text,))
        stud = mycursor.fetchone()
        mycursor.execute(f"INSERT INTO skip(std_id, name, surname, fathername, class, email, subject, date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (stud[0], stud[1], stud[2], stud[3], stud[5], stud[4], tsubject[0], almatyZone.strftime(dt_format),))
        mydb.commit()
        msg = bot.send_message(message.chat.id, "Ученик добавлен в список отутствующих", reply_markup = service)
        bot.register_next_step_handler(msg, teacher_class_otmetka)
    else:
        bot.send_message(message.chat.id, 'Ошибка')
        start(message)

def teacher_class(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Выбор класса отменен')
        start(message)
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
            reply_message += f"{studentss[i][0]}: {studentss[i][1]} {studentss[i][2]}\n"
        bot.send_message(message.chat.id, reply_message)
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row(group)
        service.row('Отмена')
        msg = bot.send_message(message.chat.id, "Введите id ученика которым хотите написать комментарий", reply_markup = service)
        bot.register_next_step_handler(msg, select_student)

def select_student(message):
    if message.text == 'Отмена':
        msg = bot.send_message(message.chat.id, 'Выбор класса отменен')
        start(message)
    elif message.text == group:
        bot.send_message(message.chat.id, 'Выбор ученика отменен')
        teacher_class(message)
    elif message.text.isdigit():
        global com_student
        com_student = message.text
        service = telebot.types.ReplyKeyboardMarkup(True, True)
        service.row(group)
        msg = bot.send_message(message.chat.id, "Напишите свой комментарий", reply_markup = service)
        bot.register_next_step_handler(msg, give_comment)
    else:
        bot.send_message(message.chat.id, 'Ошибка')
        start(message)

def give_comment(message):
    if message.text == group:
        bot.send_message(message.chat.id, 'Написание комментария отменено')
        teacher_class(message)
    else:
        mycursor.execute(f"SELECT teleid, name, surname FROM students WHERE id = %s",(com_student,))
        result = mycursor.fetchone()
        mycursor.execute(f"INSERT INTO warns(teleid, name, surname, comment, subject) VALUES(%s, %s, %s, %s, %s)", (result[0], result[1], result[2], message.text, tsubject[0],))
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
        bot.send_message(message.chat.id, 'Отправка сообщения отменена')
        start(message)
    elif message.text == 'Да':
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
