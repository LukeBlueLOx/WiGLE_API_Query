import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import pandas as pd

#Authorization - replace: ***** with Your credentials
API_Name = "*****" 
API_Token = "*****"

# Date format for the API: yyyyMMdd
output_date = "2024-08-09"
start_time = datetime(2024, 8, 9, 0, 0, 0)  # Start of the day
end_time = datetime(2024, 8, 9, 23, 59, 59)  # End of the day

# Convert to the appropriate format for the API
start_time_str = start_time.strftime('%Y%m%d%H%M%S')
end_time_str = end_time.strftime('%Y%m%d%H%M%S')

# Common parameters with restricted geographic range
common_params = {
    "latrange1": "51.098",  # Lower latitude boundary
    "latrange2": "51.3418",  # Upper latitude boundary
    "longrange1": "15.5404", # Lower longitude boundary
    "longrange2": "16.4159", # Upper longitude boundary
    "firsttime": start_time_str,  # Start time for data filtering
    "lasttime": end_time_str,     # End time for data filtering
    "resultsPerPage": "1000"      # Maximum number of results per page
}

base_url = "https://api.wigle.net/api/v2"

def fetch_data(endpoint, params):
    url = f"{base_url}/{endpoint}/search"
    all_results = []
    search_after = None  # For pagination

    while True:
        if search_after:
            params['searchAfter'] = search_after

        response = requests.get(url, auth=HTTPBasicAuth(API_Name, API_Token), params=params)
        response.raise_for_status()  # Error checking
        data = response.json()

        results = data.get('results', [])
        if not results:
            break

        all_results.extend(results)

        search_after = data.get('searchAfter')
        if not search_after or len(results) < int(params['resultsPerPage']):
            break

    return all_results

# Fetching WiFi data
print(f"Fetching WiFi data for {output_date}")
wifi_params = common_params.copy()
wifi_data = fetch_data("network", wifi_params)
wifi_df = pd.DataFrame(wifi_data)
wifi_df.to_csv(f'wifi_data_{output_date}.csv', index=False, encoding='utf-8')
print(f"WiFi data has been saved to 'wifi_data_{output_date}.csv'.")

# Fetching Bluetooth data
print(f"Fetching Bluetooth data for {output_date}")
bluetooth_params = common_params.copy()
bluetooth_data = fetch_data("bluetooth", bluetooth_params)
bluetooth_df = pd.DataFrame(bluetooth_data)
bluetooth_df.to_csv(f'bluetooth_data_{output_date}.csv', index=False, encoding='utf-8')
print(f"Bluetooth data has been saved to 'bluetooth_data_{output_date}.csv'.")

# Fetching Cell data
print(f"Fetching Cell data for {output_date}")
cell_params = common_params.copy()
cell_data = fetch_data("cell", cell_params)
cell_df = pd.DataFrame(cell_data)
cell_df.to_csv(f'cell_data_{output_date}.csv', index=False, encoding='utf-8')
print(f"Cell data has been saved to 'cell_data_{output_date}.csv'.")
