import telebot
import requests
import time
import schedule
from threading import Thread

API_TOKEN = '7957194530:AAGrSmukhzG1xgnaQGZfcD8v-BcEe8LTLqo'
bot = telebot.TeleBot(API_TOKEN)

server_url = 'http://192.168.1.36:5000'  # Адрес API сервера

# Создать кошелек с миллиардом монет (предполагается, что кошелек уже создан вручную)
sender_address = '4d460c73bdd79548c36a3905668117e346abfb300c02f5e3903ab0d9281740aa'

# Адрес, на который будут отправляться монеты
recipient_address = None
last_send_time = 0

# Словарь для хранения сообщений на разных языках
messages = {
    'en': {
        'welcome': "Welcome to the testnet giver bot! Use the /test_give command to send coins to the specified address.",
        'ask_address': "Which address should the coins be sent to?",
        'address_set': "Recipient address set: {}",
        'sending_coins': "Sending 200 coins...",
        'send_success': "Coins successfully sent to address {}",
        'send_error': "Error sending coins: {}",
        'choose_language': "Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык"
    },
    'es': {
        'welcome': "¡Bienvenido al bot de prueba de red! Usa el comando /test_give para enviar monedas a la dirección especificada.",
        'ask_address': "¿A qué dirección se deben enviar las monedas?",
        'address_set': "Dirección del destinatario establecida: {}",
        'sending_coins': "Enviando 200 monedas...",
        'send_success': "Monedas enviadas con éxito a la dirección {}",
        'send_error': "Error al enviar monedas: {}",
        'choose_language': "Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык"
    },
    'ru': {
        'welcome': "Добро пожаловать в тестнет гивер бот! Используйте команду /test_give, чтобы отправить монеты на указанный адрес.",
        'ask_address': "На какой адрес отправить монеты?",
        'address_set': "Адрес получателя установлен: {}",
        'sending_coins': "Отправка 200 монет...",
        'send_success': "Монеты успешно отправлены на адрес {}",
        'send_error': "Ошибка при отправке монет: {}",
        'choose_language': "Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык"
    },
    'uk': {
        'welcome': "Ласкаво просимо до тестнет гівер бота! Використовуйте команду /test_give, щоб відправити монети на вказану адресу.",
        'ask_address': "На яку адресу відправити монети?",
        'address_set': "Адресу одержувача встановлено: {}",
        'sending_coins': "Відправка 200 монет...",
        'send_success': "Монети успішно відправлені на адресу {}",
        'send_error': "Помилка відправлення монет: {}",
        'choose_language': "Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык"
    }
}

# Словарь для хранения выбранного языка пользователей
user_languages = {}

# Функция для отправки монет
def send_coins(chat_id):
    global recipient_address, last_send_time
    user_lang = user_languages.get(chat_id, 'en')
    if recipient_address:
        response = requests.post(f'{server_url}/transfer', json={
            'user_id': chat_id,
            'sender': sender_address,
            'recipient': recipient_address,
            'amount': 200
        })
        result = response.json()
        if 'error' in result:
            try:
                bot.send_message(chat_id, messages[user_lang]['send_error'].format(result['error']))
            except Exception as e:
                print(f"Не удалось отправить сообщение об ошибке: {e}")
        else:
            last_send_time = time.time()
            try:
                bot.send_message(chat_id, messages[user_lang]['send_success'].format(recipient_address))
            except Exception as e:
                print(f"Не удалось отправить сообщение об успешной транзакции: {e}")

# Функция для планировщика задач
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика в отдельном потоке
schedule_thread = Thread(target=run_schedule)
schedule_thread.start()

# Обработчик команды /start для приветственного сообщения и выбора языка
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add('English', 'Español', 'Русский', 'Українська')
    msg = bot.reply_to(message, messages['en']['choose_language'], reply_markup=markup)
    bot.register_next_step_handler(msg, set_language)

def set_language(message):
    chat_id = message.chat.id
    if message.text == 'English':
        user_languages[chat_id] = 'en'
    elif message.text == 'Español':
        user_languages[chat_id] = 'es'
    elif message.text == 'Русский':
        user_languages[chat_id] = 'ru'
    elif message.text == 'Українська':
        user_languages[chat_id] = 'uk'
    else:
        user_languages[chat_id] = 'en'

    bot.send_message(chat_id, messages[user_languages[chat_id]]['welcome'])

# Обработчик команды /test_give для установки адреса получателя и отправки монет
@bot.message_handler(commands=['test_give'])
def ask_address(message):
    user_lang = user_languages.get(message.chat.id, 'en')
    msg = bot.reply_to(message, messages[user_lang]['ask_address'])
    bot.register_next_step_handler(msg, process_address)

def process_address(message):
    global recipient_address
    user_lang = user_languages.get(message.chat.id, 'en')
    recipient_address = message.text
    bot.reply_to(message, messages[user_lang]['address_set'].format(recipient_address))
    bot.send_message(message.chat.id, messages[user_lang]['sending_coins'])
    send_coins(message.chat.id)

bot.polling()