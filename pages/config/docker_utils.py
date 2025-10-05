"""
Docker-compatible utils functions that don't depend on frontend.st_utils
This file provides the same functionality as utils.py but without Docker dependencies
"""

import os

def get_env_path():
    """Get the path to the .env file"""
    # In Docker container, look for env in multiple possible locations
    possible_paths = [
        '/home/dashboard/.env',
        '/home/dashboard/frontend/.env', 
        os.path.join(os.path.dirname(__file__), '../../../.env'),
        '.env'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If no .env file found, return default path
    return os.path.join(os.path.dirname(__file__), '../../../.env')

def parse_env_value(key, env_path=None):
    """Parse environment variable from .env file"""
    if env_path is None:
        env_path = get_env_path()
    
    try:
        if not os.path.exists(env_path):
            # Fallback to os.environ
            return os.environ.get(key)
            
        with open(env_path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith(f'{key}='):
                value = line[len(f'{key}='):].strip()
                return value
    except Exception:
        # Fallback to os.environ
        return os.environ.get(key)
    
    return None

def is_us_deployment():
    """Check if this is a US deployment"""
    value = parse_env_value('US_DEPLOYMENT')
    return value and value.lower() == 'true'

def get_default_connector():
    """Get the default connector name"""
    if is_us_deployment():
        value = parse_env_value('DEFAULT_CONNECTOR')
        if value:
            return value.strip().strip('"')
        # Fallback to kraken for US deployment
        return 'kraken'
    else:
        value = parse_env_value('DEFAULT_CONNECTOR')
        if value:
            return value.strip().strip('"')
        # Fallback to binance for global deployment
        return 'binance'

def get_connector_list():
    """Get the list of available connectors"""
    connector_list = []
    global_extras = ["gate_io", "gate_io_perpetual", "kucoin", "ascend_ex"]
    
    if is_us_deployment():
        value = parse_env_value('CONNECTOR_LIST_US')
        if value:
            value = value.strip('[]')
            connector_list = [x.strip().strip('"') for x in value.split(',')]
        if not connector_list:
            connector_list = ["kraken", "binance"]
    else:
        value = parse_env_value('CONNECTOR_LIST_GLOBAL')
        if value:
            value = value.strip('[]')
            connector_list = [x.strip().strip('"') for x in value.split(',')]
        # Optionally append extras
        for item in global_extras:
            if item not in connector_list:
                connector_list.append(item)
    
    if not connector_list:
        connector_list = ["binance"]
        if not is_us_deployment():
            connector_list += global_extras
    
    # Check EXCLUDE_TEST_CONNECTORS
    exclude_tests = parse_env_value('EXCLUDE_TEST_CONNECTORS')
    exclude_tests = exclude_tests and exclude_tests.lower() == 'true'
    
    if not exclude_tests:
        tests_value = parse_env_value('CONNECTOR_LIST_TESTS')
        if tests_value:
            tests_value = tests_value.strip('[]')
            test_connectors = [x.strip().strip('"') for x in tests_value.split(',') if x.strip()]
            connector_list += [c for c in test_connectors if c and c not in connector_list]
    
    return connector_list

def get_connector_list_tests():
    """Returns test connector list"""
    tests_value = parse_env_value('CONNECTOR_LIST_TESTS')
    if tests_value:
        tests_value = tests_value.strip('[]')
        return [x.strip().strip('"') for x in tests_value.split(',') if x.strip()]
    return [
        "paper_trade",
        "bybit_perpetual_testnet",
        "derive_perpetual_testnet", 
        "hyperliquid_perpetual_testnet",
        "binance_perpetual_testnet",
        "hyperliquid_testnet",
        "ndax_testnet",
        "dexalot_testnet",
        "bybit_testnet",
        "vertex_testnet",
        "derive_testnet"
    ]  # Default fallback with all testnet connectors