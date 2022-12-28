from telebot import TeleBot
from telebot import types
import sqlite3


class DataBase:
    def __init__(self):
        self.database = sqlite3.connect('movie.db', check_same_thread=False)

    def manager(self, sql, *args,
                commit: bool = False,
                fetchone: bool = False,
                fetchall: bool = False):
        with self.database as db:
            cursor = db.cursor()
            cursor.execute(sql, args)
            if commit:
                result = db.commit()
            if fetchone:
                result = cursor.fetchone()
            if fetchall:
                result = cursor.fetchall()
            return result

    def create_members_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS members(
            member_id TEXT PRIMARY KEY,
            member_username TEXT 
        )'''
        self.manager(sql, commit=True)

    def create_movie_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS movie(
            movie_id TEXT PRIMARY KEY,
            movie_name TEXT,
            movie_year INTEGER
        )'''
        self.manager(sql, commit=True)

    def create_admin_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS admin(
                    admin_id TEXT PRIMARY KEY,
                    admin_name TEXT,
                    phone_number INTEGER
                )'''
        self.manager(sql, commit=True)

    def get_user_by_id(self, member_id):
        sql = '''
        SELECT * FROM members WHERE member_id == ?
        '''
        return self.manager(sql, member_id, fetchone=True)

    def get_admin_by_id(self, admin_id):
        sql = '''SELECT * FROM admin WHERE admin_id == ?'''
        return self.manager(sql, admin_id, fetchone=True)

    def register_user(self, member_id, member_username):
        sql = '''INSERT INTO members(member_id, member_username) VALUES (?,?)'''
        self.manager(sql, member_id, member_username, commit=True)

    def get_movie_id(self, movie_id):
        sql = '''SELECT * FROM movie WHERE movie_id = ?'''
        return self.manager(sql, movie_id, fetchone=True)

    def get_movie_name_by_id(self, movie_id):
        sql = '''SELECT movie_name FROM movie WHERE movie_id = ?'''
        return self.manager(sql, movie_id, fetchone=True)

    def insert_movie_info(self, movie_id, movie_name, movie_year):
        sql = '''INSERT INTO movie(movie_id, movie_name, movie_year) VALUES (?,?,?)'''
        self.manager(sql, movie_id, movie_name, movie_year, commit=True)

    def register_admin(self, telegram_id, full_name, contact):
        sql = '''
        INSERT INTO admin(admin_id, admin_name, phone_number) VALUES (?,?,?)
        '''
        self.manager(sql, telegram_id, full_name, contact, commit=True)

    def delete_movie_info(self, movie_id):
        sql = '''DELETE FROM movie WHERE movie_id = ?'''
        self.manager(sql, movie_id, commit=True)


db = DataBase()

TOKEN = '5266391817:AAGzN3q4hauPMH9CwmBxmCVxwjRbHN7_FJ0'
bot = TeleBot(TOKEN)


# Buttons

def generate_contact_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton(text='Отправить контакт', request_contact=True)
    markup.add(btn)
    return markup


def start_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    link_keyboard1 = types.InlineKeyboardButton(text='1-й Канал', url='https://t.me/+sY2-yZtzFW9kMDAy')
    check_keyboard = types.InlineKeyboardButton(text='Проверить✅', callback_data='check')
    markup.add(link_keyboard1, check_keyboard)
    return markup


def generate_movie():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton(text='Кнопка для фильмов')
    markup.add(btn)
    return markup


def generate_movie_add_remove():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(text='Добавить фильм')
    btn2 = types.KeyboardButton(text='Удалить фильм')
    markup.add(btn1, btn2)
    return markup


# Message handlers

def start_admin_register(message: types.Message):
    chat_id = message.chat.id
    user = db.get_admin_by_id(chat_id)
    if user:
        bot.send_message(chat_id, 'Добро пожаловать админ')
        bot.send_message(chat_id, 'Выбероите две функции которые вы хотите сделать',
                         reply_markup=generate_movie_add_remove())
    else:
        msg = bot.send_message(chat_id, 'Отправьте свою имя и фамилию')
        bot.register_next_step_handler(msg, get_name_ask_phone)


def get_name_ask_phone(message: types.Message):
    chat_id = message.chat.id
    full_name = message.text
    msg = bot.send_message(chat_id, 'Отправьте свой номер телефона, нажав на кнопку',
                           reply_markup=generate_contact_button())
    bot.register_next_step_handler(msg, finish_register, full_name)


def finish_register(message: types.Message, full_name):
    chat_id = message.chat.id
    contact = message.contact.phone_number
    db.register_admin(chat_id, full_name, contact)
    bot.send_message(chat_id, 'Регистрация прошла успешно', reply_markup=generate_movie_add_remove())


def start_register(message: types.Message):
    chat_id = message.chat.id
    user = db.get_user_by_id(chat_id)
    if user:
        bot.send_message(chat_id, 'Нажмите на кнопку чтобы продолжить.', reply_markup=generate_movie())
    else:
        bot.send_message(chat_id, 'Пожалуйста подпишитесь на каналы ниже чтобы пройти регистрацию!',
                         reply_markup=start_markup())


movie_data = []


def first_input(message: types.Message):
    chat_id = message.chat.id
    text1 = message.text
    movie_data.append(text1)
    msg = bot.send_message(chat_id, 'Введите название фильма')
    bot.register_next_step_handler(msg, second_input)


def second_input(message: types.Message):
    chat_id = message.chat.id
    text2 = message.text
    movie_data.append(text2)
    msg = bot.send_message(chat_id, 'Введите год выхода фильма')
    bot.register_next_step_handler(msg, third_input)


def third_input(message: types.Message):
    chat_id = message.chat.id
    text3 = message.text
    movie_data.append(text3)
    db.insert_movie_info(movie_data[0], movie_data[1], movie_data[2])
    movie_data.clear()
    bot.send_message(chat_id, 'Фильм добавлен, хотите добавить ещё?', reply_markup=generate_movie_add_remove())


def delete_by_id(message: types.Message):
    chat_id = message.chat.id
    text = message.text
    db.delete_movie_info(text)
    bot.send_message(chat_id, 'Фильм был удален. Хотите сделать что-то ещё?', reply_markup=generate_movie_add_remove())


@bot.message_handler(regexp='Кнопка для фильмов')
def show_main_menu(message: types.Message):
    chat_id = message.chat.id
    text = '''Введите код фильма'''
    msg = bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, answer_to_text)


@bot.message_handler(regexp='Добавить фильм')
def show_main_menu(message: types.Message):
    chat_id = message.chat.id
    text = '''Добавьте код фильма'''
    msg = bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, first_input)


@bot.message_handler(regexp='Удалить фильм')
def show_main_menu(message: types.Message):
    chat_id = message.chat.id
    text = '''Напишите код фильма чтобы удалить'''
    msg = bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, delete_by_id)


def answer_to_text(message: types.Message):
    chat_id = message.chat.id
    text = message.text
    movie_id = db.get_movie_id(text)
    if movie_id:
        name = db.get_movie_name_by_id(text)
        bot.send_message(chat_id, f'Название фильма: {name}')
        bot.send_message(chat_id, 'Какой фильм вы хотите узнать?', reply_markup=generate_movie())
    else:
        bot.send_message(chat_id, 'Не удалось найти фильм', reply_markup=generate_movie())


# Commands

@bot.message_handler(commands=['start', 'register_admin', 'admin'])
def command_start(message: types.Message):
    chat_id = message.chat.id
    if message.text == '/start':
        text = 'Здравствуйте. Вас приветствует лучший бот по фильмам'
        bot.send_message(chat_id, text)
        start_register(message)
    elif message.text == '/register_admin':
        start_admin_register(message)
    elif message.text == '/admin':
        user = db.get_admin_by_id(chat_id)
        if user:
            bot.send_message(chat_id, 'Выберите две функции который вы хотите сделать',
                             reply_markup=generate_movie_add_remove())
        else:
            pass


# Callback side

def check(call: types.CallbackQuery):
    status = ['creator', 'administrator', 'member']
    for i in status:
        if i == bot.get_chat_member(chat_id='-1001887414087', user_id=call.message.chat.id).status:
            bot.send_message(call.message.chat.id, 'Спасибо что подписались на каналы!', reply_markup=generate_movie())
            chat_id = call.message.chat.id
            username = call.message.chat.username
            db.register_user(chat_id, username)
            break
        else:
            bot.send_message(call.message.chat.id, 'Подпишитесь на каналы.', reply_markup=start_markup())


@bot.callback_query_handler(func=lambda call: True)
def subscribe_check(call: types.CallbackQuery):
    if call.data == 'check':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        check(call)


bot.polling(none_stop=True)
