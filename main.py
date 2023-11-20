import threading
import schedule
import telebot
import time
import sqlite3
import requests
import json


bot_token = ""
steam_token = ""
bot = telebot.TeleBot(bot_token)
connection = None
status_dict = {0: 'Не в сети', 1: 'В сети', 2: 'Не беспокоить', 3: 'Нет на месте'}
print('Бот запущен')


def get_connection():
    global connection
    if connection is None:
        connection = sqlite3.connect('main.db', check_same_thread=False)
    return connection


def init_db(force: bool = False):
    connection_db = get_connection()
    cursor = connection_db.cursor()
    if force:
        cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        id          INTEGER PRIMARY KEY AUTOINCREMENT
                    UNIQUE,
        user_id     INTEGER NOT NULL
                    UNIQUE,
        full_name   TEXT NOT NULL,
        username    TEXT,
        isadmin     INTEGER NOT NULL
                    DEFAULT (0)
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS cheking(
            id          INTEGER PRIMARY KEY AUTOINCREMENT
                        UNIQUE,
            user_id     INTEGER NOT NULL,
            steam_id    INTEGER NOT NULL,
            lastsended  TEXT,
            cur_status  INTEGER,
            last_seen   INTEGER
            )
        ''')
    connection_db.commit()


init_db()
conn = get_connection()
c = conn.cursor()


def req(steamid):
    r = requests.get(
        f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_token}&steamids={steamid}")
    result = json.loads(r.content)["response"]["players"][0]
    return result


def check_online(steamid):
    return req(steamid)['personastate']


@bot.message_handler(commands=['start'])  # Отлавливаем команду старт
def start(message):
    info = c.execute('SELECT * FROM users WHERE user_id=?', (message.chat.id,))
    if info.fetchone() is None:
        user_name = message.from_user.full_name
        c.execute("INSERT INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
                  (message.chat.id, message.from_user.full_name, message.from_user.username))
        conn.commit()
        bot.send_message(message.chat.id, 'Привет ' + user_name)
        bot.send_message(message.chat.id, 'Я бот который позволяет проверять статус аккаунтов Steam. '
                                          'Пришли мне интересующий тебя steam id и я пришлю тебе его статус')
    else:
        bot.send_message(message.chat.id, 'Ты уже зарегистрирован!')


@bot.message_handler(commands=['add'])
def add_steamid(message):
    try:
        rawtext = message.text
        steamid = rawtext.replace('/add ', '')
        res = req(steamid)
        c.execute("INSERT INTO cheking (user_id, steam_id, cur_status) VALUES (?, ?, ?)", (message.chat.id, steamid, res['personastate']))
        conn.commit()
        bot.send_message(message.chat.id, f'SteamID {steamid} успешно добавлен')
    except:
        bot.send_message(message.chat.id, 'Вы ввели неверный steamid!')


@bot.message_handler(commands=['remove'])
def remove_steamid(message):
    rawtext = message.text
    steamid = rawtext.replace('/remove ', '')
    c.execute("DELETE FROM cheking WHERE steam_id=(?)", (steamid,))
    conn.commit()
    bot.send_message(message.chat.id, f'SteamID {steamid} успешно удален')


@bot.message_handler(commands=['list'])
def list_all(message):
    c.execute("SELECT steam_id FROM cheking WHERE user_id=(?)", (message.chat.id,))
    array = c.fetchall()
    if array:
        text = ""
        for i in range(len(array)):
            res = req(array[i][0])
            text = f"{text} {i+1}. <code>{res['steamid']}</code> - <a href=\"{res['profileurl']}\">" \
                   f"{res['personaname']}</a> - {status_dict[check_online(res['steamid'])]}\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 'Вы еще ничего не добавили')


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, '/start - Starts the bot \n/add - Add new steamid to list '
                                      '\n/remove - Remove steamid from list \n/list - Check all steamids you add')


def run_continuously(interval=1):  # Хз как но оно работает, запускает отложку в фоне
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


def checkstatus():
    c.execute("SELECT user_id, steam_id, cur_status FROM cheking")
    array = c.fetchall()
    for i in range(len(array)):
        res = req(array[i][1])
        if res['personastate'] != array[i][2]:
            if res['personastate'] == 0:
                print(f"{str(res['steamid'])} - {res['personaname']} - Не в сети")
                bot.send_message(array[i][0], f"{str(res['steamid'])} - {res['personaname']} - Не в сети")
                c.execute(f"UPDATE cheking SET cur_status = ('0') WHERE steam_id = ({array[i][1]})")
            elif res['personastate'] == 1:
                try:
                    print(
                        f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']}")
                    bot.send_message(array[i][0],
                                     f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']}")
                    c.execute(f"UPDATE cheking SET cur_status = ('1') WHERE steam_id = ({array[i][1]})")
                except:
                    print(f"{str(res['steamid'])} - {res['personaname']} - В сети")
                    bot.send_message(array[i][0], f"{str(res['steamid'])} - {res['personaname']} - В сети")
                    c.execute(f"UPDATE cheking SET cur_status = ('1') WHERE steam_id = ({array[i][1]})")
            elif res['personastate'] == 2:
                try:
                    print(
                        f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']} и включен статус не беспокоить")
                    bot.send_message(array[i][0],
                                     f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']}"
                                     f"и включен статус не беспокоить")
                    c.execute(f"UPDATE cheking SET cur_status = ('2') WHERE steam_id = ({array[i][1]})")
                except:
                    print(f"{str(res['steamid'])} - {res['personaname']} - Не беспокоить")
                    bot.send_message(array[i][0], f"{str(res['steamid'])} - {res['personaname']} -  В сети")
                    c.execute(f"UPDATE cheking SET cur_status = ('2') WHERE steam_id = ({array[i][1]})")
            elif res['personastate'] == 3:
                try:
                    print(
                        f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']}, но его нет на месте")
                    bot.send_message(array[i][0],
                                     f"{str(res['steamid'])} - {res['personaname']} - Играет в {res['gameextrainfo']}, "
                                     f"но его нет на месте")
                    c.execute(f"UPDATE cheking SET cur_status = ('3') WHERE steam_id = ({array[i][1]})")
                except:
                    print(f"{str(res['steamid'])} - {res['personaname']} - Нет на месте")
                    bot.send_message(array[i][0],
                                     f"{str(res['steamid'])} - {res['personaname']} - Нет на месте")
                    c.execute(f"UPDATE cheking SET cur_status = ('3') WHERE steam_id = ({array[i][1]})")
    conn.commit()


checkstatus()
# schedule.every(30).seconds.do(checkstatus)
schedule.every(5).minutes.do(checkstatus)
stop_run_continuously = run_continuously()

bot.polling(none_stop=True)
