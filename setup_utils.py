#!/usr/bin/env python3
"""
Setup script utilities that import from the consolidated docker_utils.py
This eliminates duplication and uses the more robust implementations
"""

import os
import sys

# Import from the consolidated docker_utils
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages', 'config'))

try:
    from pages.config.docker_utils import (
        get_env_path,
        parse_env_value, 
        is_us_deployment,
        get_default_connector as get_default_connector_name,  # Alias for backward compatibility
        get_connector_list,
        get_connector_list_tests
    )
except ImportError:
    # Fallback implementations if import fails
    def get_env_path():
        return os.path.join(os.path.dirname(__file__), '.env')
    
    def parse_env_value(key, env_path=None):
        if env_path is None:
            env_path = get_env_path()
        try:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f'{key}='):
                            return line[len(f'{key}='):].strip()
        except Exception:
            pass
        return os.environ.get(key)
    
    def is_us_deployment():
        value = parse_env_value('US_DEPLOYMENT')
        return value and value.lower() == 'true'
    
    def get_default_connector_name():
        return 'kraken' if is_us_deployment() else 'binance'
    
    def get_connector_list():
        return ["kraken","binance_us"] if is_us_deployment() else ["binance", "gate_io", "kucoin"]
    
    def get_connector_list_tests():
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
        ]

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python setup_utils_standalone.py <function_name>")
        sys.exit(1)
    
    function_name = sys.argv[1]
    
    if function_name == "get_connector_list":
        result = get_connector_list()
        # Format as JSON array for .env file compatibility
        print(json.dumps(result) if isinstance(result, list) else result)
    elif function_name == "get_default_connector_name":
        print(get_default_connector_name())
    elif function_name == "get_connector_list_tests":
        result = get_connector_list_tests()
        # Format as JSON array for .env file compatibility
        print(json.dumps(result) if isinstance(result, list) else result)
    else:
        print(f"Unknown function: {function_name}")
        sys.exit(1)