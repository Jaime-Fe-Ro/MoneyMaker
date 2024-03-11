import json
import os
from operator import concat

logs_folder = 'test_logs'


def create_logs_folder_if_not_existing():
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)


def save_account_dict(account_dict, file_name):
    with open(file_name, 'w') as file:
        json.dump(account_dict, file, indent=4)
        print("Account dictionary saved")


def validate_rpc_endpoint(rpc_endpoint, account_dict, file_name):
    if not rpc_endpoint.startswith("https://eth1.lava.build/lava-referer") or len(rpc_endpoint) != 74:
        rpc_endpoint = input("Invalid RPC endpoint, it doesn't start right or length is wrong. Try again: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)
    return rpc_endpoint


def validate_wallet_address(wallet_address, account_dict, file_name):
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        wallet_address = input("Invalid wallet address, it doesn't start with '0x' or length is wrong. Try again: ")
        stop_running_check(wallet_address, account_dict, file_name)
        wallet_address = validate_wallet_address(wallet_address, account_dict, file_name)
        wallet_address = check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)
    return wallet_address


def validate_private_key(private_key, account_dict, file_name):
    if len(private_key) != 64:
        private_key = input("Invalid private key, try again: ")
        stop_running_check(private_key, account_dict, file_name)
        validate_private_key(private_key, account_dict, file_name)
        check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
    return private_key


def check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name):
    if rpc_endpoint in [v["rpc_endpoint"] for v in account_dict.values()]:
        rpc_endpoint = input("Duplicate RPC endpoint, try again: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)
    return rpc_endpoint


def check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name):
    if wallet_address in account_dict:
        wallet_address = input("Duplicate wallet address, try again: ")
        stop_running_check(wallet_address, account_dict, file_name)
        wallet_address = validate_wallet_address(wallet_address, account_dict, file_name)
        wallet_address = check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)
    return wallet_address


def check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name):
    if private_key in [v["private_key"] for v in account_dict.values()]:
        private_key = input("Duplicate private key, try again: ")
        stop_running_check(private_key, account_dict, file_name)
        validate_private_key(private_key, account_dict, file_name)
        check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
    return private_key


def add_account_to_dictionary(account_dict, wallet_address, private_key, rpc_endpoint):
    account_dict[wallet_address] = {"private_key": private_key, "rpc_endpoint": rpc_endpoint}
    print(f"Account added to dictionary")


def main():
    create_logs_folder_if_not_existing()
    file_name = concat(input("Enter the file name: "), ".json")
    account_dict = {}
    accounts_to_add = 50
    count = 1
    while count <= accounts_to_add:
        # RPC endpoint
        rpc_endpoint = input("(input 'end' to exit) Enter the RPC endpoint: ")
        stop_running_check(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = validate_rpc_endpoint(rpc_endpoint, account_dict, file_name)
        rpc_endpoint = check_if_rpc_endpoint_already_in_account_dictionary(rpc_endpoint, account_dict, file_name)

        # Wallet address
        wallet_address = input("(input 'end' to exit) Enter the wallet address: ")
        stop_running_check(wallet_address, account_dict, file_name)
        wallet_address = validate_wallet_address(wallet_address, account_dict, file_name)
        wallet_address = check_if_wallet_address_already_in_account_dictionary(wallet_address, account_dict, file_name)

        # Private key
        # private_key = input("Enter the private key: ")
        # stop_running_check(private_key, account_dict, file_name)
        # private_key = validate_private_key(private_key, account_dict, file_name)
        # check_if_private_key_already_in_account_dictionary(private_key, account_dict, file_name)
        private_key = "d7aa36d14d42a043718b77a747406fbfe307bbb2483d0f55bbea30ac1ddf5c1b"

        # Add account to dictionary
        add_account_to_dictionary(account_dict, wallet_address, private_key, rpc_endpoint)
        save_account_dict(account_dict, file_name)
        count += 1


def stop_running_check(user_input, account_dict, file_name):
    if user_input.lower() == 'end':
        save_account_dict(account_dict, file_name)
        exit()


main()
