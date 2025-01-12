from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import uuid
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import requests
import GPUtil
import platform
import psutil
import logging
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

blockchain = []
transactions = []
validators = []

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize a thread pool executor for asynchronous operations
executor = ThreadPoolExecutor(max_workers=4)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect('blockchain.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS wallets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        address TEXT NOT NULL,
                        balance INTEGER NOT NULL,
                        name TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        type TEXT NOT NULL,
                        counterparty TEXT NOT NULL,
                        amount INTEGER NOT NULL
                    )''')
        conn.commit()

init_db()

def generate_hash():
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()

def create_genesis_block():
    genesis_block = {
        'index': 0,
        'timestamp': time.time(),
        'previous_hash': '0',
        'transactions': [],
        'nonce': 0,
        'hash': hashlib.sha256('genesis_block'.encode()).hexdigest()
    }
    blockchain.append(genesis_block)

create_genesis_block()

def add_wallet_to_db(user_id: str, address: str, balance: int, name: str = None):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO wallets (user_id, address, balance, name) VALUES (?, ?, ?, ?)', 
                  (user_id, address, balance, name))
        conn.commit()

def get_wallets_from_db(user_id: str):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT address, balance, name FROM wallets WHERE user_id = ?', (user_id,))
        wallets = c.fetchall()
        logging.debug(f'Wallets for user {user_id}: {wallets}')
        return [{'address': wallet['address'], 'balance': wallet['balance'], 'name': wallet['name']} for wallet in wallets]

def delete_wallet_from_db(user_id: str, address: str):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            logging.debug(f'Deleting wallet {address} for user {user_id}...')
            c.execute('DELETE FROM wallets WHERE user_id = ? AND address = ?', (user_id, address))
            conn.commit()
            logging.debug(f'Wallet {address} for user {user_id} has been deleted.')
    except Exception as e:
        logging.error(f'Error deleting wallet {address} for user {user_id}: {str(e)}')

def send_notification_to_bot(user_id, address, amount):
    bot_api_url = 'https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendPhoto'
    message = f'You have received {amount}$ to wallet {address}'
    photo_path = os.path.join('Icons', 'receive_icon.png')
    
    with open(photo_path, 'rb') as photo:
        payload = {
            'chat_id': user_id,
            'caption': message
        }
        files = {
            'photo': photo
        }
        response = requests.post(bot_api_url, data=payload, files=files)
        
    if response.status_code != 200:
        logging.error(f"Failed to send notification to bot: {response.text}")

def update_wallet_balance(address: str, amount: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE wallets SET balance = balance + ? WHERE address = ?', (amount, address))
        conn.commit()

def add_transaction_to_db(address: str, timestamp: float, tx_type: str, counterparty: str, amount: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO transactions (address, timestamp, type, counterparty, amount) VALUES (?, ?, ?, ?, ?)',
                  (address, timestamp, tx_type, counterparty, amount))
        conn.commit()

    if tx_type == 'received':
        c.execute('SELECT user_id FROM wallets WHERE address = ?', (address,))
        user = c.fetchone()
        if user:
            user_id = user['user_id']
            send_notification_to_bot(user_id, address, amount)

def get_transactions_from_db(address: str):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT timestamp, type, counterparty, amount FROM transactions WHERE address = ?', (address,))
        transactions = c.fetchall()
        return [{'timestamp': tx['timestamp'], 'type': tx['type'], 'counterparty': tx['counterparty'], 'amount': tx['amount']} for tx in transactions]

def calculate_block_reward(block_index: int) -> int:
    base_reward = 50
    reward_reduction_interval = 100
    reward = max(base_reward - (block_index // reward_reduction_interval), 1)
    return reward

def get_gpu_info():
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        return {
            'name': gpu.name,
            'load': f'{gpu.load * 100:.2f}%',
            'memory_total': f'{gpu.memoryTotal} MB',
            'memory_used': f'{gpu.memoryUsed} MB',
            'memory_free': f'{gpu.memoryFree} MB'
        }
    return {}

def get_disk_info():
    disks = psutil.disk_partitions()
    disk_info = []
    for disk in disks:
        usage = psutil.disk_usage(disk.mountpoint)
        disk_info.append({
            'device': disk.device,
            'mountpoint': disk.mountpoint,
            'fstype': disk.fstype,
            'total': f'{round(usage.total / (1024.0 ** 3))} GB',
            'used': f'{round(usage.used / (1024.0 ** 3))} GB',
            'free': f'{round(usage.free / (1024.0 ** 3))} GB',
            'percent': f'{usage.percent} %'
        })
    return disk_info

def get_network_speed():
    # Example values, replace with actual internet speed or use speedtest-cli library
    return '100Mbps'

def get_system_info():
    gpu_info = get_gpu_info()
    return {
        'cpu': platform.processor(),
        'gpu': gpu_info,
        'ram': f'{round(psutil.virtual_memory().total / (1024.0 ** 3))} GB',
        'disk': get_disk_info(),
        'network_speed': get_network_speed(),
        'hashes_performed': 0,
        'blocks_mined': 0,
        'start_time': time.time()
    }

@app.route('/transfer_coins', methods=['POST'])
def transfer_coins():
    data = request.get_json()
    wallet_address = data['wallet_address']
    amount = data['amount']

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT 1 FROM wallets WHERE address = ?', (wallet_address,))
        wallet = c.fetchone()
        if not wallet:
            return jsonify({'error': 'Invalid wallet address'}), 400

        c.execute('UPDATE wallets SET balance = balance + ? WHERE address = ?', (amount, wallet_address))
        conn.commit()

    timestamp = time.time()
    executor.submit(add_transaction_to_db, wallet_address, timestamp, 'received', 'game_reward', amount)

    return jsonify({'message': 'Coins transferred successfully'})

@app.route('/create_wallet', methods=['POST'])
def create_wallet():
    user_id = str(request.json['user_id'])
    wallets = get_wallets_from_db(user_id)
    if len(wallets) >= 5:
        return jsonify({'error': 'Maximum number of wallets reached'}), 400
    new_address = generate_hash()
    name = request.json.get('name')
    executor.submit(add_wallet_to_db, user_id, new_address, 100, name)
    return jsonify({'address': new_address, 'balance': 100, 'name': name})

@app.route('/create_wallet_with_balance', methods=['POST'])
def create_wallet_with_balance():
    user_id = str(request.json['user_id'])
    balance = request.json['balance']
    new_address = generate_hash()
    name = request.json.get('name')
    executor.submit(add_wallet_to_db, user_id, new_address, balance, name)
    return jsonify({'address': new_address, 'balance': balance, 'name': name})

@app.route('/wallets/<user_id>', methods=['GET'])
def get_user_wallets(user_id):
    wallets = get_wallets_from_db(user_id)
    logging.debug(f'Wallets for user {user_id}: {wallets}')
    return jsonify(wallets)

@app.route('/balance/<user_id>/<address>', methods=['GET'])
def check_balance(user_id, address):
    wallets = get_wallets_from_db(user_id)
    for wallet in wallets:
        if wallet['address'] == address:
            return jsonify({'balance': wallet['balance']})
    return jsonify({'error': 'Invalid address'}), 400

@app.route('/transaction_history/<address>', methods=['GET'])
def get_transaction_history(address):
    transactions = get_transactions_from_db(address)
    if transactions:
        return jsonify(transactions)
    return jsonify({'error': 'No transaction history for the specified address'}), 400

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    user_id = str(data['user_id'])
    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT balance FROM wallets WHERE address = ?', (sender,))
        sender_wallet = c.fetchone()
        if not sender_wallet or sender_wallet['balance'] < amount:
            return jsonify({'error': 'Insufficient funds or invalid sender address'}), 400

        c.execute('SELECT 1 FROM wallets WHERE address = ?', (recipient,))
        recipient_wallet = c.fetchone()
        if not recipient_wallet:
            return jsonify({'error': 'Invalid recipient address'}), 400

        c.execute('UPDATE wallets SET balance = balance - ? WHERE address = ?', (amount, sender))
        c.execute('UPDATE wallets SET balance = balance + ? WHERE address = ?', (amount, recipient))
        conn.commit()

    timestamp = time.time()
    executor.submit(add_transaction_to_db, sender, timestamp, 'sent', recipient, amount)
    executor.submit(add_transaction_to_db, recipient, timestamp, 'received', sender, amount)

    return jsonify({'message': 'Transaction successful'})

@app.route('/delete_wallet', methods=['POST'])
def delete_wallet():
    data = request.get_json()
    user_id = str(data['user_id'])
    address = data['address']
    logging.debug(f"Received request to delete wallet {address} for user {user_id}")
    
    existing_wallets = get_wallets_from_db(user_id)
    if any(wallet['address'] == address for wallet in existing_wallets):
        executor.submit(delete_wallet_from_db, user_id, address)
        return jsonify({'message': 'Wallet deleted'})
    else:
        return jsonify({'error': 'Wallet not found'}), 400

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain)

@app.route('/transactions', methods=['GET'])
def get_transactions():
    return jsonify(transactions)

@app.route('/add_block', methods=['POST'])
def add_block():
    new_block = request.get_json()
    
    required_fields = ['index', 'timestamp', 'previous_hash', 'transactions', 'nonce', 'hash', 'miner_address']
    if not all(field in new_block for field in required_fields):
        return jsonify({'error': 'Invalid block structure'}), 400
    
    if new_block['index'] != len(blockchain):
        return jsonify({'error': 'Invalid block index'}), 400
    
    if new_block['previous_hash'] != blockchain[-1]['hash']:
        return jsonify({'error': 'Invalid previous hash'}), 400

    block_data = str(new_block['index']) + json.dumps(new_block['transactions'], sort_keys=True) + new_block['previous_hash'] + str(new_block['nonce'])
    calculated_hash = hashlib.sha256(block_data.encode("ascii")).hexdigest()
    if calculated_hash != new_block['hash']:
        return jsonify({'error': 'Invalid block hash'}), 400

    blockchain.append(new_block)
    transactions.clear()
    
    miner_address = new_block['miner_address']
    block_index = new_block['index']
    reward_amount = calculate_block_reward(block_index)
    update_wallet_balance(miner_address, reward_amount)
    add_transaction_to_db(miner_address, time.time(), 'mining_reward', 'blockchain', reward_amount)
    
    return jsonify({'message': 'Block added to blockchain', 'block': new_block})

@app.route('/validators', methods=['GET'])
def get_validators():
    current_time = time.time()
    for validator in validators:
        validator['uptime'] = current_time - validator['start_time']
    return jsonify(validators)

@app.route('/add_validator', methods=['POST'])
def add_validator():
    data = request.get_json()
    validator_info = {
        'wallet_address': data['wallet_address'],
        'ton_wallet_address': data['ton_wallet_address'],
        'hashes_performed': data.get('hashes_performed', 0),
        'blocks_mined': data.get('blocks_mined', 0),
        'start_time': data.get('start_time', time.time()),
        'system_info': get_system_info(),
    }
    validators.append(validator_info)
    return jsonify({'message': 'Validator successfully registered', 'validators': validators})

@app.route('/update_validator', methods=['POST'])
def update_validator():
    data = request.get_json()
    for validator in validators:
        if validator['wallet_address'] == data['wallet_address']:
            validator['hashes_performed'] = data['hashes_performed']
            validator['blocks_mined'] = data['blocks_mined']
            
            if 'start_time' in data:
                validator['start_time'] = data['start_time']
            
            if 'system_info' in data:
                validator['system_info'] = data['system_info']
            else:
                return jsonify({'error': "'system_info' key is missing in the request data"}), 400

            return jsonify({'message': 'Validator info updated', 'validators': validators})
    return jsonify({'error': 'Validator not found'}), 404

@app.route('/validator_stats/<wallet_address>', methods=['GET'])
def get_validator_stats(wallet_address):
    for validator in validators:
        if validator['wallet_address'] == wallet_address:
            current_time = time.time()
            uptime = current_time - validator['start_time']
            avg_working_time = uptime / max(validator['blocks_mined'], 1)
            
            stats = {
                'wallet_address': validator['wallet_address'],
                'ton_wallet_address': validator['ton_wallet_address'],
                'hashes_performed': validator['hashes_performed'],
                'blocks_mined': validator['blocks_mined'],
                'average_working_time': avg_working_time,
                'total_working_time': uptime,
                'system_info': validator['system_info']
            }
            return jsonify(stats)
    return jsonify({'error': 'Validator not found'}), 404

@app.route('/telegram_message', methods=['POST'])
def handle_telegram_message():
    data = request.get_json()
    message = data['message']
    # Обработка сообщения от валидатора
    return jsonify({'message': 'Message processed'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)