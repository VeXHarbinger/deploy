import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
def get_env_path():
    return os.path.join(os.path.dirname(__file__), '../../../.env')

import os
import datetime
import pandas as pd
import streamlit as st
from frontend.st_utils import get_backend_api_client


def get_max_records(days_to_download: int, interval: str) -> int:
    conversion = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440}
    unit = interval[-1]
    quantity = int(interval[:-1])
    return int(days_to_download * 24 * 60 / (quantity * conversion[unit]))

def parse_env_value(key, env_path=None):
    if env_path is None:
        env_path = get_env_path()
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    value = line.split('=', 1)[1].strip()
                    return value
    except Exception:
        pass
    return None

def is_us_deployment():
    us_deployment = parse_env_value('US_DEPLOYMENT')
    return us_deployment and us_deployment.lower() == 'true'

def get_default_connector():
    if is_us_deployment():
        value = parse_env_value('DEFAULT_CONNECTOR')
        if value:
            return value.strip().strip('"')
        # Fallback to binance_us for US deployment
        return 'binance_us'
    else:
        value = parse_env_value('DEFAULT_CONNECTOR')
        if value:
            return value.strip().strip('"')
        # Fallback to binance for global deployment
        return 'binance'

def get_connector_list():
    connector_list = []
    global_extras = ["gate_io", "gate_io_perpetual", "kucoin", "ascend_ex"]
    if is_us_deployment():
        value = parse_env_value('CONNECTOR_LIST_US')
        if value:
            value = value.strip('[]')
            connector_list = [x.strip().strip('"') for x in value.split(',')]
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

@st.cache_data
def get_candles(connector_name=None, trading_pair="BTC-USDT", interval="1m", days=7):
    backend_client = get_backend_api_client()
    if connector_name is None:
        connector_name = get_default_connector()
    # Use the market_data.get_candles_last_days method
    candles = backend_client.market_data.get_candles_last_days(
        connector_name=connector_name,
        trading_pair=trading_pair,
        days=days,
        interval=interval
    )
    # Convert the response to DataFrame (response is a list of candles)
    df = pd.DataFrame(candles)
    if not df.empty and 'timestamp' in df.columns:
        df.index = pd.to_datetime(df.timestamp, unit='s')
    return df
