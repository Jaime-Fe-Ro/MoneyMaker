import asyncio
import json
import os
import sys
from datetime import datetime
from aiohttp import TCPConnector, ClientSession, ClientOSError


def get_time_now():
    return datetime.now().strftime('%d-%m-%Y %H-%M-%S')


def log_setup():
    log_directory_name = 'logs'
    main_logs_path = os.path.join(os.getcwd(), log_directory_name)
    log_file_name = f"{get_time_now()}.txt"
    main_logs_file_path = os.path.join(main_logs_path, log_file_name)
    return main_logs_file_path


class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


def get_dictionary():
    accounts_file_path = os.path.join(os.getcwd(), 'Accounts.json')
    try:
        with open(accounts_file_path, 'r') as file:
            accounts = json.load(file)
            return accounts
    except FileNotFoundError as e:
        print(f"La cagaste. Vete al grupo y pega este mensaje {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"La cagaste. Vete al grupo y pega este mensaje {e}")
        return None


def modify_dictionary(dictionary):
    rpc_prefix = "https://near.lava.build/lava-referer-"
    for address, info in dictionary.items():
        rpc_endpoint = info.get('rpc_endpoint')
        if rpc_endpoint.startswith('https://eth1.lava.build/lava-referer-'):
            info['rpc_endpoint'] = rpc_endpoint.replace('https://eth1.lava.build/lava-referer-', rpc_prefix)
    return dictionary


def get_wallets_and_endpoints(selected_account_dictionary):
    wallets_and_endpoints = {}
    for wallet_address, details in selected_account_dictionary.items():
        rpc_endpoint = details.get('rpc_endpoint')
        wallets_and_endpoints[wallet_address] = rpc_endpoint
    return wallets_and_endpoints


async def eth_check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            balance = int(str(result['result']), 16) / 1e18
            print(f"{wallet_index + 1}: {wallet_address} -> balance: {balance} ETH")
            success_counter[wallet_address] = success_counter.get(wallet_address, 0) + 1
        except Exception as e:
            print(f" eth_check_wallet_balance Error converting balance: {e}")
    else:
        print(f"Error checking balance: {wallet_index + 1}: {wallet_address}")


async def eth_check_gas_price(session, wallet_address, rpc_endpoint, success_counter, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 2}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            gas_price = int(result['result'], 16) / 1e9  # Adjusted for Gwei
            print(f"{wallet_index + 1}: {wallet_address} -> gas price: {gas_price} Gwei")
            success_counter[wallet_address] = success_counter.get(wallet_address, 0) + 1
        except Exception as e:
            print(f"Error converting gas price: {e}")
    else:
        print(f"Error checking gas price: {wallet_index + 1}: {wallet_address}")


async def eth_check_block_number(session, wallet_address, rpc_endpoint, success_counter, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 3}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            block_number = int(result['result'], 16)
            print(f"{wallet_index + 1}: {wallet_address} -> block number: {block_number}")
            success_counter[wallet_address] = success_counter.get(wallet_address, 0) + 1
        except Exception as e:
            print(f"Error converting block number: {e}")
    else:
        print(f"Error checking block number: {wallet_index + 1}: {wallet_address}")


async def near_check_wallet_balance(session, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "query",
        "params": {
            "request_type": "view_account",
            "finality": "final",
            "account_id": "test.near"
        },
        "id": 1}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            print(f"{wallet_index + 1}: {wallet_address} -> balance checked")
            success_counter[wallet_address] = success_counter.get(wallet_address, 0) + 1
        except Exception as e:
            print(f"Error checking balance: {e}")
    else:
        print(f"Error checking balance: {wallet_index + 1}: {wallet_address}")


async def near_check_network_status(session, rpc_endpoint, success_counter, wallet_address, wallet_index):
    payload = {
        "jsonrpc": "2.0",
        "method": "status",
        "params": {},
        "id": 2}
    result = await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index)
    if result is not None and 'result' in result:
        try:
            print(f"{wallet_index + 1}: {wallet_address} -> Checked network status")
            success_counter[wallet_address] = success_counter.get(wallet_address, 0) + 1
        except Exception as e:
            print(f"Error checking network status: {e}")
    else:
        print(f"Error checking network status: {wallet_index + 1}: {wallet_address}")


async def fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index):
    try:
        async with session.post(str(rpc_endpoint), json=payload) as response:
            if response.status == 429:
                print(f"ERROR. Too Many Requests. Waiting 1 second for the server to recover. {wallet_index + 1}: {wallet_address}")
                await asyncio.sleep(1)
                return None

            if response.status != 200:
                print(f"ERROR. Error fetching data: HTTP status {response.status}. {wallet_index + 1}: {wallet_address}")
                return None

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                print(f"ERROR. Unexpected response content type: {content_type}, {wallet_index + 1}: {wallet_address}")
                return None

            return await response.json()
    except ClientOSError:
        print(f"ERROR. A network error occurred. Retrying after 1 second. {wallet_index + 1}: {wallet_address}")
        await asyncio.sleep(1)
        return None
    except Exception as e:
        print(f"ERROR. Error fetching data: {e}. {wallet_index + 1}: {wallet_address}")
        return None


async def main(eth, near):
    connector = TCPConnector(limit=10, limit_per_host=1)
    loop_counter = 0
    success_counter = {}
    start_time = datetime.now()
    print(f"\nStart time: {start_time}")
    async with ClientSession(connector=connector) as session:
        while True:
            print("\nStarting loop: ", loop_counter)
            tasks = []
            for wallet_index, (wallet_address, rpc_endpoint) in enumerate(eth.items()):
                tasks.append(eth_check_wallet_balance(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
                tasks.append(eth_check_gas_price(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
                tasks.append(eth_check_block_number(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
            for wallet_index, (wallet_address, rpc_endpoint) in enumerate(near.items()):
                tasks.append(near_check_network_status(
                    session, rpc_endpoint, success_counter, wallet_address, wallet_index))
                tasks.append(near_check_wallet_balance(
                    session, rpc_endpoint, success_counter, wallet_address, wallet_index))
            await asyncio.gather(*tasks)
            loop_counter += 1
            time_elapsed = (datetime.now() - start_time).total_seconds()
            rps = sum(success_counter.values()) / time_elapsed if time_elapsed > 0 else 0
            rps = round(rps, 2)
            print(f"\n - Loop finished - ")
            print(f"Total Success count: {sum(success_counter.values())}")
            print(f"Time Elapsed: {round(time_elapsed, 2)}")
            print(f"Requests per second: {rps}\n")
            for wallet_address, count in success_counter.items():
                print(f"Wallet {wallet_address} made {count} successful requests.")
            print("\n-------------------------------------------------------------------\n\n")


def setup():
    log_file_path = log_setup()
    sys.stdout = Logger(log_file_path)
    eth_dictionary = get_wallets_and_endpoints(get_dictionary())
    near_dictionary = get_wallets_and_endpoints(modify_dictionary(get_dictionary()))
    return eth_dictionary, near_dictionary


def run():
    eth_dict, near_dict = setup()
    asyncio.run(main(eth_dict, near_dict))


run()
