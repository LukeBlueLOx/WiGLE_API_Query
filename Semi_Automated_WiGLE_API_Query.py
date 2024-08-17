from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time
import urllib.parse as urlparse
import yaml
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime

# Define function to calculate the map viewport range
def calculate_viewport(center_lat, center_lon, zoom):
    zoom_ranges = {
        17: {'lat_range': 0.00085, 'lon_range': 0.003395},
        16: {'lat_range': 0.00205, 'lon_range': 0.00695},
        15: {'lat_range': 0.0041, 'lon_range': 0.01385},
        14: {'lat_range': 0.00815, 'lon_range': 0.02765},
        13: {'lat_range': 0.0163, 'lon_range': 0.0557},
        12: {'lat_range': 0.0326, 'lon_range': 0.1115},
    }

    if zoom not in zoom_ranges:
        raise ValueError(f"Unsupported zoom level: {zoom}")

    lat_range = zoom_ranges[zoom]['lat_range']
    lon_range = zoom_ranges[zoom]['lon_range']

    lat_min = center_lat - lat_range
    lat_max = center_lat + lat_range
    lon_min = center_lon - lon_range
    lon_max = center_lon + lon_range

    return lat_min, lat_max, lon_min, lon_max

# Firefox settings
options = Options()
options.headless = False  # Set to True if you want to run Firefox without GUI
service = Service(executable_path='geckodriver')

# Start the browser
driver = webdriver.Firefox(service=service, options=options)

# Login loop
while True:
    driver.get('https://wigle.net/login?destination=/map')
    
    # Log in
    print("Please log in...")
    while True:
        try:
            # User logs in manually
            input("Log in and select ROI on the map (currently only for zoom levels: 17-12), then press Enter to continue...")
            
            # Check if the map page is loaded
            if "map" in driver.current_url:
                print("Logged in successfully!")
                break
            else:
                print("Login failed. Please try again.")
                retry = input("Do you want to try again? (Y/N): ")
                if retry.strip().lower() == 'n':
                    print("Exiting program.")
                    driver.quit()
                    exit()
                else:
                    # Clear session and try again
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
                    driver.get('https://wigle.net/login?destination=/map')
                    time.sleep(5)
        except Exception as e:
            print(f"Error: {e}. Please try again.")
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.get('https://wigle.net/login?destination=/map')
            time.sleep(5)

    # Main program loop
    while True:
        # Get the current URL
        current_url = driver.current_url

        # Parse the URL to extract `maplat`, `maplon`, `mapzoom` values
        parsed_url = urlparse.urlparse(current_url)
        query_params = urlparse.parse_qs(parsed_url.query)

        center_lat = float(query_params['maplat'][0])
        center_lon = float(query_params['maplon'][0])
        zoom = int(query_params['mapzoom'][0])

        # Calculate the map viewport range
        lat_min, lat_max, lon_min, lon_max = calculate_viewport(center_lat, center_lon, zoom)

        # Display results
        print(f"Zoom: {zoom}")
        print(f"Map center: latitude {center_lat}, longitude {center_lon}")
        print(f"Map viewport range:")
        print(f"Latitude from {lat_min} to {lat_max}")
        print(f"Longitude from {lon_min} to {lon_max}")

        # Ask for date and time
        output_date = input("Enter date (YYYY-MM-DD): ")
        start_time_str = input("Enter start time (HH:MM:SS): ")
        end_time_str = input("Enter end time (HH:MM:SS): ")

        # Process date and time
        start_time = datetime.strptime(f"{output_date} {start_time_str}", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{output_date} {end_time_str}", "%Y-%m-%d %H:%M:%S")

        # Convert to API format
        start_time_str = start_time.strftime('%Y%m%d%H%M%S')
        end_time_str = end_time.strftime('%Y%m%d%H%M%S')

        # Common parameters for the API
        common_params = {
            "latrange1": str(lat_min),  # Lower latitude boundary
            "latrange2": str(lat_max),  # Upper latitude boundary
            "longrange1": str(lon_min), # Lower longitude boundary
            "longrange2": str(lon_max), # Upper longitude boundary
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
            
                with open("config.yaml", "r") as cr:
                    config_vals = yaml.full_load(cr)
                API_Name = config_vals['API_Name']
                API_Token = config_vals['API_Token']
                
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

        # Fetch WiFi data
        print(f"Fetching WiFi data for {output_date}")
        wifi_params = common_params.copy()
        wifi_data = fetch_data("network", wifi_params)
        wifi_df = pd.DataFrame(wifi_data)
        wifi_df.to_csv(f'wifi_data_{output_date}.csv', index=False, encoding='utf-8')
        print(f"WiFi data has been saved to 'wifi_data_{output_date}.csv'.")

        # Fetch Bluetooth data
        print(f"Fetching Bluetooth data for {output_date}")
        bluetooth_params = common_params.copy()
        bluetooth_data = fetch_data("bluetooth", bluetooth_params)
        bluetooth_df = pd.DataFrame(bluetooth_data)
        bluetooth_df.to_csv(f'bluetooth_data_{output_date}.csv', index=False, encoding='utf-8')
        print(f"Bluetooth data has been saved to 'bluetooth_data_{output_date}.csv'.")

        # Fetch Cell data
        print(f"Fetching Cell data for {output_date}")
        cell_params = common_params.copy()
        cell_data = fetch_data("cell", cell_params)
        cell_df = pd.DataFrame(cell_data)
        cell_df.to_csv(f'cell_data_{output_date}.csv', index=False, encoding='utf-8')
        print(f"Cell data has been saved to 'cell_data_{output_date}.csv'.")

        # Ask the user if they want to choose and confirm a new ROI
        user_input = input("Do you want to select and confirm a new ROI? (Enter to confirm, N to exit): ")
        
        if user_input.strip().lower() == 'n':
            print("Exiting program.")
            break  # Exit the main loop

    # End the program after breaking out of the main loop
    print("Closing browser...")
    driver.quit()
    break  # Exit the login loop
