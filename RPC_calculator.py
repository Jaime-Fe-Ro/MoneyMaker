# Constants
NEAR_RPC_calls_per_second = 30
ETH_RPC_calls_per_second = 30
hours = 2*23
accounts = 100

number_of_rpc_call_types = 5

# Calculation
calls_per_second = NEAR_RPC_calls_per_second + ETH_RPC_calls_per_second
total_calls = calls_per_second * 3600 * hours
rpc_calls_per_loop = accounts * number_of_rpc_call_types
total_rpc_calls_per_account = (total_calls / rpc_calls_per_loop) * number_of_rpc_call_types
print(f"Total loops: {total_rpc_calls_per_account}")
