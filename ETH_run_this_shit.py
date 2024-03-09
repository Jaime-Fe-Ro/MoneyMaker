import asyncio
import json
import os
import sys
from asyncio import sleep
from datetime import datetime
from aiohttp import TCPConnector, ClientSession


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


def get_dictionary(file_name):
    accounts_file_path = os.path.join(os.getcwd(), file_name)
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
        await eth_check_wallet_balance(session, wallet_address, rpc_endpoint, success_counter, wallet_index)


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
        await eth_check_gas_price(session, wallet_address, rpc_endpoint, success_counter, wallet_index)


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
        await eth_check_block_number(session, wallet_address, rpc_endpoint, success_counter, wallet_index)


async def fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index, retry_count=0):
    try:
        async with session.post(str(rpc_endpoint), json=payload) as response:
            if response.status == 429:
                print(f" - Too many requests - ")
                if retry_count >= 800:
                    print(f" {retry_count} retries failed in a row, slowed down.")
                    await sleep(10)
                    return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index,
                                            retry_count + 1)
                await sleep(0.5)
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index, retry_count + 1)

            if response.status != 200:
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index,
                                        retry_count + 1)

            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index,
                                        retry_count + 1)
            print(response.json())
            return await response.json()

    except Exception as e:
        print(f"Algo va mal, ralentizando el programa 0.5s/request, manda este mensaje al grupo. Error: {e}")
    if retry_count < 800:
        return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index, retry_count + 1)
    else:
        print(f" {retry_count} retries failed in a row, slowed down.")
        await sleep(10)
        return await fetch_data(session, payload, rpc_endpoint, wallet_address, wallet_index,
                                retry_count + 1)


async def main(eth):
    connector = TCPConnector(limit=50, limit_per_host=10)
    loop_counter = 1
    accounts_looped = len(eth)
    success_counter = {}
    start_time = datetime.now()
    print(f"\nStarting ETH looper at: {start_time}")
    async with ClientSession(connector=connector) as session:
        while True:
            print("\nStarting loop ", loop_counter)
            tasks = []
            for wallet_index, (wallet_address, rpc_endpoint) in enumerate(eth.items()):
                tasks.append(eth_check_wallet_balance(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
                tasks.append(eth_check_gas_price(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
                tasks.append(eth_check_block_number(
                    session, wallet_address, rpc_endpoint, success_counter, wallet_index))
            await asyncio.gather(*tasks)
            loop_counter += 1
            time_elapsed = (datetime.now() - start_time).total_seconds()
            rps = sum(success_counter.values()) / time_elapsed if time_elapsed > 0 else 0
            rps = round(rps, 2)
            rpw = sum(success_counter.values()) / accounts_looped
            rpw = round(rpw, 0)
            print(f"\n - Loop finished - ")
            print(f"Total Success count: {sum(success_counter.values())}")
            print(f"Time Elapsed: {round(time_elapsed, 2)}")
            print(f"Requests per second: {rps}\n")
            print(f"Requests per wallet: {rpw}")
            print("\n\n-------------------------------------------------------------------\n")


def run():
    log_file_path = log_setup()
    sys.stdout = Logger(log_file_path)
    eth_dict = get_wallets_and_endpoints(get_dictionary('Accounts.json'))
    asyncio.run(main(eth_dict))


run()
