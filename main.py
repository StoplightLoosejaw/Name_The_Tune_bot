import os
from telebot import apihelper
from database import TuneEngine
from telebot import types
import random

apihelper.proxy = {'https': 'socks5h://198.27.75.152:1080'}
bot = os.getenv("TOKEN")

db = TuneEngine()
db.setup()

genres_markup = types.ReplyKeyboardMarkup(selective=True)
all_genres = ['rap', 'pop', 'Русские треки']
genres_markup.row(*all_genres)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not db.get_items('ALL_USERS', 'USER_ID', message.from_user.id):
        db.new_player(message.from_user.id)
        bot.reply_to(message, 'Добро пожаловать в Угадай мелодию, и с вами ее бессменный ведущий')
        bot.send_photo(message.from_user.id, photo='https://i.ytimg.com/vi/Z38sARsCX_U/hqdefault.jpg')
    if db.get_items('ALL_USERS', 'GAME_PHASE', message.from_user.id) == 0:
        genre(message)
    if db.get_items('ALL_USERS', 'GAME_PHASE', message.from_user.id) == 1:
        db.game_begin(message.from_user.id)
        db.update_field('ALL_USERS', 'GAME_PHASE', 1, message.from_user.id)
        markup = types.ReplyKeyboardMarkup(selective=True)
        answ_buttons = [
                        db.get_items('CURRENT_GAME', 'CORRECT_ARTIST', message.from_user.id),
                        db.get_items('CURRENT_GAME', 'INCORRECT_ARTISTS', message.from_user.id).split(',')[0],
                        db.get_items('CURRENT_GAME', 'INCORRECT_ARTISTS', message.from_user.id).split(',')[1],
                        db.get_items('CURRENT_GAME', 'INCORRECT_ARTISTS', message.from_user.id).split(',')[2]
                        ]
        random.shuffle(answ_buttons)
        for i in answ_buttons:
            markup.row(i)
        bot.reply_to(message, 'Слушаем трек \n {}'.format(db.get_items('CURRENT_GAME', 'LYRICS', message.from_user.id)),
                     reply_markup=markup)
        bot.register_next_step_handler(message, check_track)


@bot.message_handler(commands=['destroy_me'])
def destroy(message):
    db.delete_row('ALL_USERS', message.from_user.id)
    db.delete_row('CURRENT_GAME', message.from_user.id)


@bot.message_handler(commands=['destroy_db'])
def destroy_table():
    db.drop()


@bot.message_handler(commands=['change_genre'])
def genre(message):
    bot.reply_to(message, 'выберите жанр', reply_markup=genres_markup)
    bot.register_next_step_handler(message, get_genre)


def get_genre(message):
    if message.text not in all_genres:
        bot.reply_to(message, 'Пожалуйста выберите один из вариков')
        bot.register_next_step_handler(message, get_genre)
    else:
        bot.reply_to(message, 'жанр выбран {}'.format(message.text), reply_markup=types.ReplyKeyboardRemove())
        db.update_field('ALL_USERS', 'GAME_PHASE', 1, message.from_user.id)
        db.update_field('CURRENT_GAME', 'GENRE', message.text, message.from_user.id)
    send_welcome(message)


def check_track(message):
    if message.text == db.get_items('CURRENT_GAME', 'CORRECT_ARTIST', message.from_user.id):
        db.player_wins(message.from_user.id)
        bot.reply_to(message, 'Победа! Это был трек {}'.format(db.get_items('CURRENT_GAME',
                                                                            'CORRECT_TRACK', message.from_user.id)),
                     reply_markup=croads_markup(message.from_user.id))
    else:
        db.player_loses(message.from_user.id)
        bot.reply_to(message, 'одна ошибка и ты ошибся. Правильный ответ {} и прекрасный трек {}'
                     .format(db.get_items('CURRENT_GAME', 'CORRECT_ARTIST', message.from_user.id),
                             db.get_items('CURRENT_GAME', 'CORRECT_TRACK', message.from_user.id)),
                     reply_markup=croads_markup(message.from_user.id))
    if db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) == 3:
        yn_markup = types.ReplyKeyboardMarkup(selective=True)
        buttons = ['Y', 'N']
        yn_markup.row(*buttons)
        bot.reply_to(message, 'Здесь есть лидербоард', reply_markup=types.ReplyKeyboardRemove())
        bot.reply_to(message, 'Вы хотите участвовать?', reply_markup=yn_markup)
        bot.register_next_step_handler(message, toggle_leaderboard)
    else:
        bot.register_next_step_handler(message, crossroads)


def toggle_leaderboard(message):
    if db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) == 0:
        db.update_field('ALL_USERS', 'LEADERBOARD_FLG', 1, message.from_user.id)
        bot.reply_to(message, 'Теперь вы есть в лидерборде', reply_markup=croads_markup(message.from_user.id))
        bot.register_next_step_handler(message, crossroads)
    elif db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) == 1:
        db.update_field('ALL_USERS', 'LEADERBOARD_FLG', 0, message.from_user.id)
        bot.reply_to(message, 'Теперь вас нет в лидерборде', reply_markup=croads_markup(message.from_user.id))
        bot.register_next_step_handler(message, crossroads)
    elif db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) in (3, 4):
        if message.text == 'Y' or message.text == 'Участвовать в лидерборде':
            db.update_field('ALL_USERS', 'LEADERBOARD_FLG', 1, message.from_user.id)
            bot.reply_to(message, 'Теперь вы есть в лидерборде. Выберите как будете отображаться')
            bot.register_next_step_handler(message, change_username)
        elif message.text == 'N':
            db.update_field('ALL_USERS', 'LEADERBOARD_FLG', 4, message.from_user.id)
            bot.reply_to(message, 'Вас нет в лидербоарде, в дальнейшем вы сможете изменить ваше решение',
                         reply_markup=croads_markup(message.from_user.id))
            bot.register_next_step_handler(message, crossroads)
        else:
            bot.reply_to(message, 'Да-да нет-нет')
            bot.register_next_step_handler(message, toggle_leaderboard)


def change_username(message):
    if db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) == 0 \
            or db.get_items('ALL_USERS', 'LEADERBOARD_FLG', message.from_user.id) == 3:
        bot.reply_to(message, 'Вы отказались от участия в лидерборде! Пожалуйста, сначала согласитесь на участие',
                     reply_markup=croads_markup(message.from_user.id))
    else:
        db.update_field('ALL_USERS', 'USER_NAME', message.text, message.from_user.id)
        bot.reply_to(message, 'Теперь вы в лидерборде отображаесь как {}'.format(message.text),
                     reply_markup=croads_markup(message.from_user.id))
    bot.register_next_step_handler(message, crossroads)


def crossroads(message):
    if message.text == 'Изменить юзернейм':
        bot.reply_to(message, 'Введите как будете отображаться')
        bot.register_next_step_handler(message, change_username)
    elif message.text == 'Участвовать в лидерборде' or message.text == 'Отказаться от лидерборда':
        toggle_leaderboard(message)
    elif message.text == 'Сменить жанр':
        genre(message)
    elif message.text == 'Показать лидерборд':
        show_lb(message)
    elif message.text == 'Eще по одной':
        send_welcome(message)
    elif message.text == 'destroy me':
        destroy(message)
    else:
        bot.reply_to(message, 'Выберите один из вариантов ответа     '.format(message.text))
        bot.register_next_step_handler(message, crossroads)


@bot.message_handler(commands=['show_lb'])
def show_lb(message):
    bot.reply_to(message, db.get_leaderboard())
    if db.get_players_position(message.from_user.id) == 3:
        bot.reply_to(message, 'Вы находитесь на {}-eм'.format(db.get_players_position(message.from_user.id)),
                     reply_markup=croads_markup(message.from_user.id))
    else:
        bot.reply_to(message, 'Вы находитесь на {}-ом'.format(db.get_players_position(message.from_user.id)),
                     reply_markup=croads_markup(message.from_user.id))
    bot.register_next_step_handler(message, crossroads)


def croads_markup(cm_id):
    base_buttons = ['Eще по одной', 'Сменить жанр']
    if db.get_items('ALL_USERS', 'LEADERBOARD_FLG', cm_id) == 0 \
            or db.get_items('ALL_USERS', 'LEADERBOARD_FLG', cm_id) == 3:
        base_buttons.append('Участвовать в лидерборде')
    else:
        base_buttons.append('Изменить юзернейм')
        base_buttons.append('Показать лидерборд')
        base_buttons.append('Отказаться от лидерборда')
    crossroads__markup = types.ReplyKeyboardMarkup(selective=True)
    for i in base_buttons:
        crossroads__markup.row(i)
    return crossroads__markup


@bot.message_handler()
def meat(message):
    bot.reply_to(message, 'Возможно что-то пошло не так, выберите что будете делать дальше',
                 reply_markup=croads_markup(message.from_user.id))
    bot.register_next_step_handler(message, crossroads)


bot.polling(none_stop=True)
