import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import pandas as pd
import time

def datetime_to_timestamp(dt):
    return int(time.mktime(dt.timetuple())) * 1000

# Time settings
start_time = datetime(2024, 8, 9, 0, 0, 0)
end_time = datetime(2024, 8, 9, 23, 59, 59)

start_timestamp = datetime_to_timestamp(start_time)
end_timestamp = datetime_to_timestamp(end_time)

# Common parameters with restricted geographic range
common_params = {
    "latrange1": "51.1894",
    "latrange2": "51.2504",
    "longrange1": "15.8701",
    "longrange2": "16.089",
    "startTime": start_timestamp,
    "endTime": end_timestamp,
    "maxresults": "1000"  # Initial results limit per page
}

base_url = "https://api.wigle.net/api/v2"

def fetch_data(endpoint, params):
    url = f"{base_url}/{endpoint}/search"
    all_results = []
    params['page'] = 1  # Initialize page number
    
    while True:
        response = requests.get(url, auth=HTTPBasicAuth('*****', '*****'), params=params)
        response.raise_for_status()  # Error checking
        data = response.json()

        results = data.get('results', [])
        if not results:
            break

        all_results.extend(results)

        if len(results) < int(params['maxresults']):
            break

        params['page'] += 1

    return all_results

# Fetching data
print("Fetching WiFi data for 2024-08-09")
wifi_params = common_params.copy()
wifi_data = fetch_data("network", wifi_params)
wifi_df = pd.DataFrame(wifi_data)
wifi_df.to_csv('wifi_data_2024_08_09.csv', index=False, encoding='utf-8')
print("WiFi data has been saved to 'wifi_data_2024_08_09.csv'.")

print("Fetching Bluetooth data for 2024-08-09")
bluetooth_params = common_params.copy()
bluetooth_data = fetch_data("bluetooth", bluetooth_params)
bluetooth_df = pd.DataFrame(bluetooth_data)
bluetooth_df.to_csv('bluetooth_data_2024_08_09.csv', index=False, encoding='utf-8')
print("Bluetooth data has been saved to 'bluetooth_data_2024_08_09.csv'.")

print("Fetching Cell data for 2024-08-09")
cell_params = common_params.copy()
cell_data = fetch_data("cell", cell_params)
cell_df = pd.DataFrame(cell_data)
cell_df.to_csv('cell_data_2024_08_09.csv', index=False, encoding='utf-8')
print("Cell data has been saved to 'cell_data_2024_08_09.csv'.")
