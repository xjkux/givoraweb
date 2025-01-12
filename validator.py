import requests
import hashlib
import time
import json
import platform
import psutil
import GPUtil
from concurrent.futures import ThreadPoolExecutor

server_url = 'http://192.168.1.36:5000'  # Замените на ваш внешний IP
MAX_NONCE = 100000000000  # Increased maximum nonce value

executor = ThreadPoolExecutor(max_workers=4)

def get_gpu_info():
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]  # Assume the first available GPU is used
        return {
            'name': gpu.name,
            'load': f'{gpu.load * 100:.2f}%',
            'memory_total': f'{gpu.memoryTotal} MB',
            'memory_used': f'{gpu.memoryUsed} MB',
            'memory_free': f'{gpu.memoryFree} MB'
        }
    return {}

def get_network_speed():
    # Example values, replace with actual internet speed or use speedtest-cli library
    return '100Mbps'

def get_system_info():
    return {
        'cpu': platform.processor(),
        'gpu': get_gpu_info(),
        'ram': f'{round(psutil.virtual_memory().total / (1024.0 ** 3))} GB',
        'disk': get_disk_info(),
        'network_speed': get_network_speed(),
    }

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

def SHA256(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()

def mine(block_number, transactions, previous_hash, prefix_zeros):
    prefix_str = '0' * prefix_zeros
    for nonce in range(MAX_NONCE):
        text = str(block_number) + transactions + previous_hash + str(nonce)
        new_hash = SHA256(text)
        if new_hash.startswith(prefix_str):
            print(f"Yay! Successfully mined bitcoins with nonce value:{nonce}")
            return new_hash, nonce

    raise BaseException(f"Couldn't find correct hash after trying {MAX_NONCE} times")

def main():
    wallet_address = input("Введите адрес вашего кошелька для получения награды: ")
    ton_wallet_address = input("Введите адрес вашего TON кошелька: ")
    validator_info = {
        'wallet_address': wallet_address,
        'ton_wallet_address': ton_wallet_address,
        'system_info': get_system_info(),
        'hashes_performed': 0,
        'blocks_mined': 0,
        'start_time': time.time()
    }

    # Register the validator on the server
    response = requests.post(f'{server_url}/add_validator', json=validator_info, verify='C:\\Users\\Tim\\server.crt')
    print(response.status_code)
    print(response.text)
    if response.status_code == 200:
        print('Validator successfully registered')

    while True:
        # Get the current blockchain and transactions from the server
        blockchain_response = requests.get(f'{server_url}/blockchain', verify='C:\\Users\\Tim\\server.crt')
        transactions_response = requests.get(f'{server_url}/transactions', verify='C:\\Users\\Tim\\server.crt')
        
        if blockchain_response.status_code == 200 and transactions_response.status_code == 200:
            blockchain = blockchain_response.json()
            transactions = transactions_response.json()
            
            # Get the last block and its hash
            last_block = blockchain[-1]
            previous_hash = last_block['hash']
            
            # Set the mining difficulty (number of leading zeros in the hash)
            difficulty = 6
            
            # Start mining a new block
            start = time.time()
            new_hash, nonce = mine(len(blockchain), json.dumps(transactions, sort_keys=True), previous_hash, difficulty)
            total_time = str((time.time() - start))
            print(f"Mining took: {total_time} seconds")
            
            new_block = {
                'index': len(blockchain),
                'timestamp': time.time(),
                'transactions': transactions,
                'previous_hash': previous_hash,
                'nonce': nonce,
                'hash': new_hash,
                'miner_address': wallet_address
            }

            response = requests.post(f'{server_url}/add_block', json=new_block, verify='C:\\Users\\Tim\\server.crt')
            if response.status_code == 200:
                validator_info['hashes_performed'] += nonce
                validator_info['blocks_mined'] += 1
                print(f'Block mined and added to the blockchain: {new_block}')
            else:
                print('Failed to add block to the blockchain')
            
            # Update validator info on the server
            response = requests.post(f'{server_url}/update_validator', json=validator_info, verify='C:\\Users\\Tim\\server.crt')
            if response.status_code != 200:
                print('Failed to update validator info')
        else:
            print('Failed to get blockchain or transactions data')

if __name__ == '__main__':
    main()