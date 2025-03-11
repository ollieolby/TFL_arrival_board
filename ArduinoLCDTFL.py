import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
import serial

# Initialize the serial connection (adjust the COM port as needed)
ser = serial.Serial('/dev/tty.usbmodem144101', 9600, timeout=1)  # Adjust 'COM3' for your setup

def get_data_from_api():
    url = "https://api.tfl.gov.uk/line/district/arrivals"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def process_data(data):
    # Select fields for the table
    selected_fields = ['vehicleId', 'stationName', 'lineName', 'platformName', 'expectedArrival', 'towards']

    # Create a list of rows with selected fields
    table_data = [{field: item[field] for field in selected_fields} for item in data]

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data)
    
    # Convert 'expectedArrival' to datetime
    df['expectedArrival'] = pd.to_datetime(df['expectedArrival'])

    # Filter DataFrame to include only specific stations
    stations_of_interest = ["Gunnersbury Underground Station", 
                            "Chiswick Park Underground Station"
                            ]
    df_filtered = df[df['stationName'].isin(stations_of_interest)]

    departure_stations = ["Richmond Underground Station", "Ealing Broadway Underground Station"]
    df_departures=df[df['stationName'].isin(departure_stations)]
    df_departures = df_departures.drop_duplicates(subset=['stationName', 'expectedArrival'])
    
    df_departures = df_departures[
        ~df_departures['towards'].str.contains('Richmond|Ealing Broadway|Westbound', case=False)
            ]
    # Add 9 minutes and rename for Ealing Broadway
    df_departures.loc[
        df_departures['stationName'] == 'Ealing Broadway Underground Station', 'stationName'
    ] = 'Chiswick Park Underground Station'
    df_departures.loc[
        df_departures['stationName'] == 'Chiswick Park Underground Station', 'expectedArrival'
    ] += pd.Timedelta(minutes=9)

    # Add 7 minutes and rename for Richmond
    df_departures.loc[
        df_departures['stationName'] == 'Richmond Underground Station', 'stationName'
    ] = 'Gunersbury Underground Station'
    df_departures.loc[
        df_departures['stationName'] == 'Gunnersbury Underground Station', 'expectedArrival'
    ] += pd.Timedelta(minutes=7)



    df_filtered=pd.concat([df_departures, df_filtered])

    df_filtered= df_filtered.drop_duplicates(subset=['vehicleId'])

    # Sort DataFrame by 'expectedArrival'
    df_filtered['is_eastbound'] = df_filtered['platformName'].str.contains('Eastbound', case=False)

    # Sort with eastbound trains first, then by expectedArrival
    df_sorted = df_filtered.sort_values(by=['is_eastbound', 'expectedArrival'], ascending=[False, True])

    # Drop the helper column as it's no longer needed
    df_sorted = df_sorted.drop(columns='is_eastbound')

    df_sorted.loc[
        df_sorted['stationName'] == 'Gunnersbury Underground Station', 'stationName'
    ] = 'Gunnersbury'

    df_sorted.loc[
        df_sorted['stationName'] == 'Chiswick Park Underground Station', 'stationName'
    ] = 'Chiswick Park'

    return df_sorted

def send_to_lcd(df):
    current_time = datetime.now(pytz.utc)
    lines_to_display = []
    lines_to_display.append('EASTBOUND,')
    show=True
    count= 1
    for _, row in df.iterrows():
        if show:
            if "Westbound" in row['platformName']:
                show=False
                lines_to_display.append('WESTBOUND,')
                count = 1
        station = row['stationName']

        arrival_time = row['expectedArrival']
        minutes_until = round((arrival_time - current_time).total_seconds() / 60)

        # Only show trains arriving in 5+ mins
        if minutes_until > 0:
            display_line = f"{count} {station[:14]},{minutes_until}min"
            lines_to_display.append(display_line)
            count+=1

    # Combine lines with a '|' delimiter and end with newline
    message = "|".join(lines_to_display)[:200] + "\n"
    ser.write(message.encode('utf-8'))
    print(f"Sent to LCD:\n{message}")



if __name__ == "__main__":
    while True:
        data = get_data_from_api()
        if data:
            df_sorted = process_data(data)
            send_to_lcd(df_sorted)
        time.sleep(30)
