import asyncio
import os
import hashlib
import json
import platform
import time

import psutil
import requests
import telebot
from telebot import types

API_TOKEN = '7853272894:AAEQFhzZKh_QgNxJnI_kDA-8oKVsRFr1u0M'
bot = telebot.TeleBot(API_TOKEN)

server_url = 'http://192.168.1.36:5000'  # Локальный сервер для примера, замените на реальный адрес сервера
owner_id = 7302464289

# Словарь для хранения текущего кошелька пользователей
current_wallet = {}
# Словарь для хранения выбранного языка пользователей
user_languages = {}

# Словарь для хранения сообщений на разных языках
messages = {
    'en': {
        'welcome': "👋 Welcome to the blockchain bot! Use the commands below to interact with your wallets.",
        'choose_language': "🌐 Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык",
        'create_wallet': "💼 Create Wallet",
        'my_wallets': "💰 My Wallets",
        'transfer': "🔄 Transfer",
        'check_balance': "💵 Check Balance",
        'transaction_history': "📜 Transaction History",
        'validators': "🛠️ Validators",
        'delete_wallet': "🗑️ Delete Wallet",
        'wallet_created': "✅ Wallet created! Address: `{}`, Balance: {}",
        'no_wallets': "⚠️ You have no wallets. Use 'Create Wallet' to create one.",
        'select_wallet': "🔍 Select a wallet to switch to:",
        'wallet_switched': "🔄 Current wallet switched to: `{}`",
        'enter_transfer_details': "✍️ Enter the recipient address and amount in the format {'address'} {'amount'}:",
        'transfer_success': "✅ Transaction successful!",
        'enter_wallet_address': "🔍 Enter the wallet address to check the balance:",
        'balance': "💵 Balance of wallet `{}`: {}",
        'transaction_history_prompt': "📜 Enter the wallet address to check the transaction history:",
        'transaction_history_empty': "⚠️ Transaction history is empty.",
        'transaction_history': "📜 Transaction history:\n",
        'transaction_sent': "📤 Sent {} to {} at {}",
        'transaction_received': "📥 Received {} from {} at {}",
        'no_wallets_to_delete': "⚠️ You have no wallets to delete.",
        'wallet_deleted': "🗑️ Wallet deleted.",
        'validators_list': "🛠️ Validators: {}",
        'not_authorized': "🚫 You are not authorized to view this information.",
        'validator_registered': "✅ Validator successfully registered.",
        'validator_registration_failed': "❌ Validator registration failed.",
        'mining_block_success': "⛏️ Block mined and added to the blockchain: {}",
        'mining_block_failed': "❌ Failed to add block to the blockchain.",
        'blockchain_data_error': "❌ Failed to retrieve blockchain or transaction data.",
        'error_occurred': "❌ An error occurred: {}",
        'invalid_format': "❌ Invalid format. Please enter data in the format 'address amount'.",
        'main_menu': "🏠 Main Menu",
        'address': "📍 Address",
        'wallets': "💼 Your wallets:\n",
        'enter_wallet_name': "✍️ Enter a name for your new wallet:",
        'wallet_not_found': "❌ Wallet not found.",
        'donate': "💸 Donate"
    },
    'es': {
        'welcome': "👋 ¡Bienvenido al bot de blockchain! Usa los comandos a continuación para interactuar con tus billeteras.",
        'choose_language': "🌐 Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык",
        'create_wallet': "💼 Crear Cartera",
        'my_wallets': "💰 Mis Carteras",
        'transfer': "🔄 Transferir",
        'check_balance': "💵 Consultar Saldo",
        'transaction_history': "📜 Historial de Transacciones",
        'validators': "🛠️ Validadores",
        'delete_wallet': "🗑️ Eliminar Cartera",
        'wallet_created': "✅ ¡Cartera creada! Dirección: `{}`, Saldo: {}",
        'no_wallets': "⚠️ No tienes carteras. Usa 'Crear Cartera' para crear una.",
        'select_wallet': "🔍 Selecciona una cartera para cambiar a ella:",
        'wallet_switched': "🔄 Cartera actual cambiada a: `{}`",
        'enter_transfer_details': "✍️ Ingrese la dirección del destinatario y la cantidad en el formato {'dirección'} {'cantidad'}:",
        'transfer_success': "✅ ¡Transacción exitosa!",
        'enter_wallet_address': "🔍 Ingrese la dirección de la cartera para consultar el saldo:",
        'balance': "💵 Saldo de la cartera `{}`: {}",
        'transaction_history_prompt': "📜 Ingrese la dirección de la cartera para consultar el historial de transacciones:",
        'transaction_history_empty': "⚠️ El historial de transacciones está vacío.",
        'transaction_history': "📜 Historial de transacciones:\n",
        'transaction_sent': "📤 Enviado {} a {} en {}",
        'transaction_received': "📥 Recibido {} de {} en {}",
        'no_wallets_to_delete': "⚠️ No tienes carteras para eliminar.",
        'wallet_deleted': "🗑️ Cartera eliminada.",
        'validators_list': "🛠️ Validadores: {}",
        'not_authorized': "🚫 No estás autorizado para ver esta información.",
        'validator_registered': "✅ Validador registrado con éxito.",
        'validator_registration_failed': "❌ Error al registrar el validador.",
        'mining_block_success': "⛏️ Bloque minado y agregado a la blockchain: {}",
        'mining_block_failed': "❌ Error al agregar el bloque a la blockchain.",
        'blockchain_data_error': "❌ Error al recuperar datos de blockchain o transacciones.",
        'error_occurred': "❌ Ocurrió un error: {}",
        'invalid_format': "❌ Formato inválido. Por favor ingrese los datos en el formato 'dirección cantidad'.",
        'main_menu': "🏠 Menú Principal",
        'address': "📍 Dirección",
        'wallets': "💼 Tus carteras:\n",
        'enter_wallet_name': "✍️ Ingrese un nombre para su nueva cartera:",
        'wallet_not_found': "❌ Cartera no encontrada.",
        'donate': "💸 Donar"
    },
    'ru': {
        'welcome': "👋 Добро пожаловать в блокчейн бот! Используйте команды ниже для взаимодействия с вашими кошельками.",
        'choose_language': "🌐 Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык",
        'create_wallet': "💼 Создать Кошелек",
        'my_wallets': "💰 Мои Кошельки",
        'transfer': "🔄 Перевод",
        'check_balance': "💵 Проверить Баланс",
        'transaction_history': "📜 История Транзакций",
        'validators': "🛠️ Валидаторы",
        'delete_wallet': "🗑️ Удалить Кошелек",
        'wallet_created': "✅ Кошелек создан! Адрес: `{}`, Баланс: {}",
        'no_wallets': "⚠️ У вас нет кошельков. Используйте 'Создать Кошелек', чтобы создать один.",
        'select_wallet': "🔍 Выберите кошелек для переключения:",
        'wallet_switched': "🔄 Текущий кошелек переключен на: `{}`",
        'enter_transfer_details': "✍️ Введите адрес получателя и сумму в формате {'адрес'} {'сумма'}:",
        'transfer_success': "✅ Транзакция успешна!",
        'enter_wallet_address': "🔍 Введите адрес кошелька, чтобы проверить баланс:",
        'balance': "💵 Баланс кошелька `{}`: {}",
        'transaction_history_prompt': "📜 Введите адрес кошелька для проверки истории транзакций:",
        'transaction_history_empty': "⚠️ История транзакций пуста.",
        'transaction_history': "📜 История транзакций:\n",
        'transaction_sent': "📤 Отправлено {} на {} в {}",
        'transaction_received': "📥 Получено {} от {} в {}",
        'no_wallets_to_delete': "⚠️ У вас нет кошельков для удаления.",
        'wallet_deleted': "🗑️ Кошелек удален.",
        'validators_list': "🛠️ Валидаторы: {}",
        'not_authorized': "🚫 Вы не авторизованы для просмотра этой информации.",
        'validator_registered': "✅ Валидатор успешно зарегистрирован.",
        'validator_registration_failed': "❌ Ошибка регистрации валидатора.",
        'mining_block_success': "⛏️ Блок намайнен и добавлен в блокчейн: {}",
        'mining_block_failed': "❌ Не удалось добавить блок в блокчейн.",
        'blockchain_data_error': "❌ Не удалось получить данные блокчейна или транзакций.",
        'error_occurred': "❌ Произошла ошибка: {}",
        'invalid_format': "❌ Неверный формат. Пожалуйста, введите данные в формате 'адрес сумма'.",
        'main_menu': "🏠 Главное Меню",
        'address': "📍 Адрес",
        'wallets': "💼 Ваши кошельки:\n",
        'enter_wallet_name': "✍️ Введите имя для вашего нового кошелька:",
        'wallet_not_found': "❌ Кошелек не найден.",
        'donate': "💸 Пожертвовать"
    },
    'uk': {
        'welcome': "👋 Ласкаво просимо до блокчейн бота! Використовуйте команди нижче для взаємодії з вашими гаманцями.",
        'choose_language': "🌐 Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык",
        'create_wallet': "💼 Створити Гаманець",
        'my_wallets': "💰 Мої Гаманці",
        'transfer': "🔄 Переказ",
        'check_balance': "💵 Перевірити Баланс",
        'transaction_history': "📜 Історія Транзакцій",
        'validators': "🛠️ Валідатори",
        'delete_wallet': "🗑️ Видалити Гаманець",
        'wallet_created': "✅ Гаманець створено! Адреса: `{}`, Баланс: {}",
        'no_wallets': "⚠️ У вас немає гаманців. Використовуйте 'Створити Гаманець', щоб створити один.",
        'select_wallet': "🔍 Виберіть гаманець для перемикання:",
        'wallet_switched': "🔄 Поточний гаманець переключено на: `{}`",
        'enter_transfer_details': "✍️ Введіть адресу одержувача та суму у форматі {'адреса'} {'сума'}:",
        'transfer_success': "✅ Транзакція успішна!",
        'enter_wallet_address': "🔍 Введіть адресу гаманця, щоб перевірити баланс:",
        'balance': "💵 Баланс гаманця `{}`: {}",
        'transaction_history_prompt': "📜 Введіть адресу гаманця для перевірки історії транзакцій:",
        'transaction_history_empty': "⚠️ Історія транзакцій порожня.",
        'transaction_history': "📜 Історія транзакцій:\n",
        'transaction_sent': "📤 Відправлено {} на {} о {}",
        'transaction_received': "📥 Отримано {} від {} о {}",
        'no_wallets_to_delete': "⚠️ У вас немає гаманців для видалення.",
        'wallet_deleted': "🗑️ Гаманець видалено.",
        'validators_list': "🛠️ Валідатори: {}",
        'not_authorized': "🚫 Ви не авторизовані для перегляду цієї інформації.",
        'validator_registered': "✅ Валідатор успішно зареєстрований.",
        'validator_registration_failed': "❌ Помилка реєстрації валідатора.",
        'mining_block_success': "⛏️ Блок намайнено та додано до блокчейну: {}",
        'mining_block_failed': "❌ Не вдалося додати блок до блокчейну.",
        'blockchain_data_error': "❌ Не вдалося отримати дані блокчейну або транзакцій.",
        'error_occurred': "❌ Сталася помилка: {}",
        'invalid_format': "❌ Невірний формат. Будь ласка, введіть дані у форматі 'адреса сума'.",
        'main_menu': "🏠 Головне Меню",
        'address': "📍 Адреса",
        'wallets': "💼 Ваші гаманці:\n",
        'enter_wallet_name': "✍️ Введіть ім'я для вашого нового гаманця:",
        'wallet_not_found': "❌ Гаманець не знайдено.",
        'donate': "💸 Пожертвувати"
    }
}

def get_message(chat_id, key):
    user_lang = user_languages.get(chat_id, 'en')
    return messages[user_lang][key]

def create_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(
        types.KeyboardButton(get_message(chat_id, 'create_wallet')),
        types.KeyboardButton(get_message(chat_id, 'my_wallets')),
        types.KeyboardButton(get_message(chat_id, 'transfer')),
        types.KeyboardButton(get_message(chat_id, 'check_balance')),
        types.KeyboardButton(get_message(chat_id, 'transaction_history')),
        types.KeyboardButton(get_message(chat_id, 'validators')),
        types.KeyboardButton(get_message(chat_id, 'delete_wallet')),
        types.KeyboardButton(get_message(chat_id, 'donate'))
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    markup.add('English', 'Español', 'Русский', 'Українська')
    msg = bot.reply_to(message, "Choose your language / Elige tu idioma / Виберіть свою мову / Выберите язык", reply_markup=markup)
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
    
    bot.send_message(chat_id, get_message(chat_id, 'welcome'), reply_markup=create_main_menu(chat_id))

@bot.message_handler(regexp='Создать кошелек|Crear Cartera|Create Wallet|Створити Гаманець')
def create_wallet(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, get_message(user_id, 'enter_wallet_name'))
    bot.register_next_step_handler(msg, process_wallet_name)

def process_wallet_name(message):
    user_id = message.from_user.id
    wallet_name = message.text
    
    # Check for invalid wallet names
    if wallet_name.lower() in ['create wallet', '/start']:
        bot.reply_to(message, "Invalid wallet name. Please choose a different name.")
        return

    response = requests.post(f'{server_url}/create_wallet', json={'user_id': user_id, 'name': wallet_name})
    wallet_info = response.json()
    if 'error' in wallet_info:
        bot.reply_to(message, wallet_info['error'])
    else:
        if user_id not in current_wallet:
            current_wallet[user_id] = wallet_info['address']
        bot.reply_to(message, get_message(user_id, 'wallet_created').format(wallet_info['address'], wallet_info['balance']), parse_mode='Markdown')

# Implementing the donation handler
@bot.message_handler(regexp='💸 Пожертвовать|💸 Donar|💸 Donate|💸 Пожертвувати')
def donate(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    donate_message = (
        "Thank you for considering a donation! You can support the bot development by sending your donations to the following addresses:\n\n"
        "💎 Donate (USDT TRC20):\n```TNvSFwVVkVbKJtZXkxBLFqKrYA3FqGVvAB```\n\n"
        "💎 Donate (USDT TON):\n```UQATIrK5enNLzvLfalGkW3dubW7Q7xuBCYlxwAeyd5Ijkd-W```"
    )
    bot.reply_to(message, donate_message, parse_mode='Markdown')

@bot.message_handler(regexp='Мои кошельки|Mis Carteras|My Wallets|Мої Гаманці')
def my_wallets(message):
    user_id = message.from_user.id
    response = requests.get(f'{server_url}/wallets/{user_id}')
    wallets = response.json()
    if wallets:
        reply = get_message(user_id, 'wallets')
        emoji_list = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "🟧"]
        for i, wallet in enumerate(wallets):
            emoji = emoji_list[i % len(emoji_list)]
            reply += f"{emoji} Name: {wallet['name']}, Address: {wallet['address']}, Balance: {wallet['balance']}\n"
        if user_id in current_wallet:
            reply += f"\n{get_message(user_id, 'wallet_switched').format(current_wallet[user_id])}"
        bot.reply_to(message, reply, parse_mode='Markdown')
        markup = types.ReplyKeyboardMarkup(row_width=2)
        for wallet in wallets:
            markup.add(types.KeyboardButton(wallet['name'] or wallet['address']))
        bot.reply_to(message, get_message(user_id, 'select_wallet'), reply_markup=markup)
    else:
        bot.reply_to(message, get_message(user_id, 'no_wallets'))

@bot.message_handler(func=lambda message: any(wallet['name'] == message.text or wallet['address'] == message.text for wallet in requests.get(f'{server_url}/wallets/{message.from_user.id}').json()))
def switch_wallet(message):
    user_id = message.from_user.id
    response = requests.get(f'{server_url}/wallets/{user_id}')
    wallets = response.json()
    for wallet in wallets:
        if wallet['name'] == message.text or wallet['address'] == message.text:
            current_wallet[user_id] = wallet['address']
            bot.reply_to(message, get_message(user_id, 'wallet_switched').format(wallet['name'] or wallet['address']), reply_markup=create_main_menu(user_id), parse_mode='Markdown')
            return
    bot.reply_to(message, get_message(user_id, 'wallet_not_found'))

@bot.message_handler(regexp='Перевод|Transferir|Transfer|Переказ')
def transfer(message):
    msg = bot.reply_to(message, get_message(message.from_user.id, 'enter_transfer_details'))
    bot.register_next_step_handler(msg, process_transfer)

def process_transfer(message):
    try:
        recipient, amount = message.text.split()
        amount = int(amount)
        user_id = message.from_user.id
        sender = current_wallet.get(user_id, None)
        if sender is None:
            bot.reply_to(message, get_message(user_id, 'no_wallets'))
            return
        
        response = requests.post(f'{server_url}/transfer', json={'user_id': user_id, 'sender': sender, 'recipient': recipient, 'amount': amount})
        result = response.json()
        
        if 'error' in result:
            bot.reply_to(message, result['error'])
        else:
            bot.reply_to(message, get_message(user_id, 'transfer_success'))
            
            # Send photo and transaction details
            photo_path = os.path.join('Icons', 'send_icon.png')
            with open(photo_path, 'rb') as photo:
                bot.send_photo(user_id, photo, caption=f"Transaction Details:\n\n"
                                                      f"Sender: {sender}\n"
                                                      f"Recipient: {recipient}\n"
                                                      f"Amount: {amount}\n"
                                                      f"Date: {time.ctime()}")
    except ValueError:
        bot.reply_to(message, get_message(message.from_user.id, 'invalid_format'))
    except Exception as e:
        bot.reply_to(message, get_message(message.from_user.id, 'error_occurred').format(str(e)))

@bot.message_handler(regexp='Проверить баланс|Consultar Saldo|Check Balance|Перевірити Баланс')
def check_balance(message):
    chat_id = message.from_user.id
    user_id = message.from_user.id
    wallets = requests.get(f'{server_url}/wallets/{user_id}').json()
    if not wallets:
        bot.reply_to(message, get_message(chat_id, 'no_wallets'))
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)
    for wallet in wallets:
        wallet_name = wallet['name'] if wallet['name'] else wallet['address']
        markup.add(types.KeyboardButton(wallet_name))

    msg = bot.reply_to(message, get_message(chat_id, 'enter_wallet_address'), reply_markup=markup)
    bot.register_next_step_handler(msg, process_check_balance)

def process_check_balance(message):
    address = None
    user_id = message.from_user.id
    wallets = requests.get(f'{server_url}/wallets/{user_id}').json()

    for wallet in wallets:
        if wallet['name'] == message.text or wallet['address'] == message.text:
            address = wallet['address']
            break

    if address is None:
        bot.reply_to(message, get_message(user_id, 'wallet_not_found'))
        return

    response = requests.get(f'{server_url}/balance/{user_id}/{address}')
    result = response.json()
    if 'error' in result:
        bot.reply_to(message, result['error'])
    else:
        balance = result.get('balance', 'N/A')
        bot.reply_to(message, get_message(user_id, 'balance').format(address, balance), parse_mode='Markdown')
        bot.send_message(message.chat.id, get_message(user_id, 'main_menu'), reply_markup=create_main_menu(user_id))

@bot.message_handler(regexp='История транзакций|Historial de Transacciones|Transaction History|Історія Транзакцій')
def transaction_history(message):
    user_id = message.from_user.id
    response = requests.get(f'{server_url}/wallets/{user_id}')
    wallets = response.json()
    if wallets:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        for wallet in wallets:
            wallet_name = wallet['name'] if wallet['name'] else wallet['address']
            markup.add(types.KeyboardButton(wallet_name))
        msg = bot.reply_to(message, get_message(user_id, 'transaction_history_prompt'), reply_markup=markup)
        bot.register_next_step_handler(msg, process_transaction_history)
    else:
        bot.reply_to(message, get_message(user_id, 'no_wallets'))
        bot.send_message(message.chat.id, get_message(user_id, 'main_menu'), reply_markup=create_main_menu(user_id))

def process_transaction_history(message):
    address = None
    user_id = message.from_user.id
    wallets = requests.get(f'{server_url}/wallets/{user_id}').json()

    for wallet in wallets:
        if wallet['name'] == message.text or wallet['address'] == message.text:
            address = wallet['address']
            break

    if address is None:
        bot.reply_to(message, get_message(user_id, 'wallet_not_found'))
        bot.send_message(message.chat.id, get_message(user_id, 'main_menu'), reply_markup=create_main_menu(user_id))
        return

    response = requests.get(f'{server_url}/transaction_history/{address}')
    result = response.json()
    if 'error' in result:
        bot.reply_to(message, result['error'])
    else:
        history = result
        if history:
            for transaction in history:
                if transaction['type'] == 'sent':
                    photo_path = os.path.join('Icons', 'send_icon.png')
                    caption = get_message(message.from_user.id, 'transaction_sent').format(transaction['amount'], transaction['counterparty'], time.ctime(transaction['timestamp']))
                elif transaction['type'] == 'received':
                    photo_path = os.path.join('Icons', 'receive_icon.png')
                    caption = get_message(message.from_user.id, 'transaction_received').format(transaction['amount'], transaction['counterparty'], time.ctime(transaction['timestamp']))
                
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(user_id, photo, caption=caption)
        else:
            bot.reply_to(message, get_message(message.from_user.id, 'transaction_history_empty'))
    bot.send_message(message.chat.id, get_message(message.from_user.id, 'main_menu'), reply_markup=create_main_menu(message.from_user.id))

@bot.message_handler(regexp='Удалить кошелек|Eliminar Cartera|Delete Wallet|Видалити Гаманець')
def delete_wallet(message):
    user_id = message.from_user.id
    response = requests.get(f'{server_url}/wallets/{user_id}')
    wallets = response.json()
    if wallets:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        for wallet in wallets:
            markup.add(types.KeyboardButton(wallet['address']))
        msg = bot.reply_to(message, get_message(user_id, 'select_wallet'), reply_markup=markup)
        bot.register_next_step_handler(msg, process_delete_wallet)
    else:
        bot.reply_to(message, get_message(user_id, 'no_wallets_to_delete'))
        bot.send_message(message.chat.id, get_message(user_id, 'main_menu'), reply_markup=create_main_menu(user_id))

def process_delete_wallet(message):
    user_id = message.from_user.id
    address = message.text
    response = requests.post(f'{server_url}/delete_wallet', json={'user_id': user_id, 'address': address})
    result = response.json()
    if 'error' in result:
        bot.reply_to(message, result['error'])
    else:
        # Remove the wallet from current_wallet if it is the current one
        if current_wallet.get(user_id) == address:
            del current_wallet[user_id]
        bot.reply_to(message, get_message(user_id, 'wallet_deleted'))
        bot.send_message(message.chat.id, get_message(user_id, 'main_menu'), reply_markup=create_main_menu(user_id))

@bot.message_handler(regexp='Валидаторы|Validadores|Validators|Валідатори')
def list_validators(message):
    if message.from_user.id == owner_id:
        response = requests.get(f'{server_url}/validators')
        validators = response.json()
        validators_info = "\n".join([str(v) for v in validators])
        bot.reply_to(message, get_message(message.from_user.id, 'validators_list').format(validators_info))
    else:
        bot.reply_to(message, get_message(message.from_user.id, 'not_authorized'))

@bot.message_handler(commands=['register_validator'])
def register_validator(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, "Введите адрес вашего кошелька для получения награды:")
    bot.register_next_step_handler(msg, process_register_validator_wallet)

def process_register_validator_wallet(message):
    user_id = message.from_user.id
    wallet_address = message.text
    msg = bot.reply_to(message, "Введите адрес вашего TON кошелька:")
    bot.register_next_step_handler(msg, process_register_validator_ton_wallet, wallet_address)

def process_register_validator_ton_wallet(message, wallet_address):
    user_id = message.from_user.id
    ton_wallet_address = message.text
    validator_info = get_system_info()
    validator_info['user_id'] = user_id
    validator_info['wallet_address'] = wallet_address
    validator_info['ton_wallet_address'] = ton_wallet_address
    response = requests.post(f'{server_url}/add_validator', json=validator_info)
    if response.status_code == 200:
        bot.reply_to(message, get_message(user_id, 'validator_registered'))
    else:
        bot.reply_to(message, get_message(user_id, 'validator_registration_failed'))
        
@bot.message_handler(commands=['mine_block'])
def mine_block(message):
    user_id = message.from_user.id
    blockchain_response = requests.get(f'{server_url}/blockchain')
    transactions_response = requests.get(f'{server_url}/transactions')

    if blockchain_response.status_code == 200 and transactions_response.status_code == 200:
        blockchain = blockchain_response.json()
        transactions = transactions_response.json()

        last_block = blockchain[-1]
        previous_hash = last_block['hash']
        difficulty = 3

        new_block, new_hash = mine_new_block(previous_hash, transactions, difficulty)
        new_block['hash'] = new_hash
        response = requests.post(f'{server_url}/add_block', json=new_block)
        if response.status_code == 200:
            bot.reply_to(message, get_message(user_id, 'mining_block_success').format(new_block))
        else:
            bot.reply_to(message, get_message(user_id, 'mining_block_failed'))
    else:
        bot.reply_to(message, get_message(user_id, 'blockchain_data_error'))

def get_system_info():
    return {
        'system_specs': {
            'cpu': platform.processor(),
            'ram': f'{round(psutil.virtual_memory().total / (1024.0 ** 3))} GB',
            'disk': f'{round(psutil.disk_usage("/").total / (1024.0 ** 3))} GB SSD'
        },
        'blocks_mined': 0,
        'mining_speed': '10 blocks/minute'
    }

def mine_new_block(previous_hash, transactions, difficulty):
    nonce = 0
    while True:
        block_data = {
            'previous_hash': previous_hash,
            'transactions': transactions,
            'nonce': nonce
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_string).hexdigest()
        if block_hash[:difficulty] == '0' * difficulty:
            return block_data, block_hash
        else:
            nonce += 1

bot.polling()