#!/usr/bin/env python
# coding: utf-8

# In[9]:


import sys
import requests
import arrow
import json
import pandas as pd
import tkinter as tk
from tkinter import scrolledtext
from geopy.geocoders import Nominatim
import pgeocode
import os
from datetime import datetime, date, time, timezone
import pytz

#set NESW function
def degrees_to_cardinal(deg):
    if deg is None: # Handle potential missing data
        return None
    # Normalize degree to be within 0-360 range
    deg = deg % 360
    if 337.5 <= deg or deg < 22.5:
        return "N"
    elif 22.5 <= deg < 67.5:
        return "NE"
    elif 67.5 <= deg < 112.5:
        return "E"
    elif 112.5 <= deg < 157.5:
        return "SE"
    elif 157.5 <= deg < 202.5:
        return "S"
    elif 202.5 <= deg < 247.5:
        return "SW"
    elif 247.5 <= deg < 292.5:
        return "W"
    elif 292.5 <= deg < 337.5:
        return "NW"
    return "N"

#get lat and lon of surf spot function
def get_lat_lon_geopy(city, state):
    geolocator = Nominatim(user_agent="surfspot")
    try:
        location = geolocator.geocode(f"{city}, {state}")
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Error with geopy: {e}")
        return None, None


def main():
    #Get current time
    start = arrow.now()
    #Get three days from now
    end = arrow.now().shift(days=3)
    #get user authorization key from stromglass.io
    authorization_key = input("Please enter API key from Stormglass: ")
    print("Please enter your surfspot by city and state")
    city = input("City: ")
    state = input("State: ")

    lat_geopy, lon_geopy = get_lat_lon_geopy(city, state)
    if lat_geopy is not None and lon_geopy is not None:
        print(f"Latitude: {lat_geopy}")
        print(f"Longitude: {lon_geopy}")
    else:
        print("Could not find coordinates for the given city and state.")
        return 1

    if authorization_key == '':
        print("No API key.")
        return 1

    #check quota of last run to not request again
    try:
        with open("quota.txt", "r") as qta:
            requestCount = int(qta.read())
    except FileNotFoundError:
        requestCount = 0

    try:
        with open("date.txt", "r") as dte:
            rdate0 = dte.read().strip()
            rdate = datetime.strptime(rdate0, '%Y-%m-%d').date()
    except FileNotFoundError:
        current_utc_datetime1 = datetime.now(timezone.utc)
        rdate = current_utc_datetime1.date()

    current_utc_datetime3 = datetime.now(timezone.utc)
    curdate = current_utc_datetime3.date()
    
    if requestCount >= 10 and rdate >= curdate:
        print("Quota limit reached, exiting.")
        return 0

    #request data from stormglass
    response = requests.get(
      'https://api.stormglass.io/v2/weather/point',
      params={
        'lat': lat_geopy,
        'lng': lon_geopy,
        'params': ','.join(['windSpeed','windDirection','gust','swellHeight','swellPeriod','swellDirection','secondarySwellHeight','secondarySwellPeriod',
          'secondarySwellDirection','waveHeight','wavePeriod','waveDirection','windWaveHeight','windWavePeriod','windWaveDirection','currentSpeed',
          'currentDirection','waterTemperature']),
        'start': start.to('UTC').timestamp(),  # Convert to UTC timestamp
        'end': end.to('UTC').timestamp()  # Convert to UTC timestamp
      },
      headers={
        'Authorization': f'{authorization_key}'
      }
    )

    #store json from sotrmglass
    json_data = response.json()

    hours = json_data.get("hours", [])

    current_utc_datetime2 = datetime.now(timezone.utc)
    current_utc_date2 = current_utc_datetime2.date()
    meta = json_data.get("meta")
    dailyQuota = meta.get("dailyQuota")
    requestCount = meta.get("requestCount")
    with open("quota.txt", "w") as qt:
        qt.write(str(requestCount))
    with open("date.txt", "w") as dt:
        dt.write(str(current_utc_date2))
    print(f"Request Count: {requestCount} Daily Quota: {dailyQuota}")

    flatlist = []
    #flatten the json data
    for hourly_data in hours:
        flathour = {}
        for header, value in hourly_data.items():
            if isinstance(value, dict):
                for header2, value2 in value.items():
                    flathour[header + " " + header2] = value2
            else:
                flathour[header] = value
        flatlist.append(flathour)
    
    print(f"\nLength of flatlist after flattening: {len(flatlist)}")

    df = pd.DataFrame(flatlist)
    #format the time
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
    #convert to Eastern or Pacific time
    timez = input("Eastern or Pacific time: ")
    if timez == "Eastern":
        zone = "America/New_York"
    elif timez == "Pacific":
        zone = "America/Los_Angeles"
    elif timez != "Eastern" or timez != "Pacific":
        print("Incorrect timezone input")
        return 1

    if 'time' in df.columns and df['time'].dt.tz is not None:
        df['time'] = df['time'].dt.tz_convert(f"{zone}")
        df['time'] = df['time'].dt.strftime('%Y-%m-%d %I:%M %p %Z')

    #convert data to nesw, ft, mph 
    for col in df.columns:
        if "direction" in col.lower():
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(degrees_to_cardinal)

    METERS_TO_FEET_FACTOR = 3.28084
    MS_TO_MPH_FACTOR = 2.23694
    C_TO_F_FACTOR_MULTIPLIER = 9/5
    C_TO_F_FACTOR_ADDITION = 32

    for col in df.columns:
        if "height" in col.lower(): # Target 'waveHeight', 'swellHeight', 'windWaveHeight'
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col] * METERS_TO_FEET_FACTOR

    for col in df.columns:
        if "speed" in col.lower() or "gust" in col.lower(): # Target 'waveHeight', 'swellHeight', 'windWaveHeight'
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col] * MS_TO_MPH_FACTOR

    for col in df.columns:
        if "temperature" in col.lower(): # Target 'waveHeight', 'swellHeight', 'windWaveHeight'
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = (df[col] * C_TO_F_FACTOR_MULTIPLIER) + C_TO_F_FACTOR_ADDITION

    numerical_cols_to_round = df.select_dtypes(include=['number']).columns.tolist()
    if 'time' in numerical_cols_to_round:
        numerical_cols_to_round.remove('time')
    df[numerical_cols_to_round] = df[numerical_cols_to_round].round(2)
    #rename and order fields
    #df = df.rename(columns={
    renameorder = { 
        # Common Column
        'time': 'Time',

        # Stormglass (SG) Model
        'windSpeed sg': 'Wind Spd (mph) SG',
        'windDirection sg': 'Wind Dir SG',
        'gust sg': 'Gust (mph) SG',
        'waveHeight sg': 'Wave Ht (ft) SG',
        'waveDirection sg': 'Wave Dir SG',
        'wavePeriod sg': 'Wave Per (s) SG',
        'swellHeight sg': 'Swell Ht (ft) SG',
        'swellDirection sg': 'Swell Dir SG',
        'swellPeriod sg': 'Swell Per (s) SG',
        'secondarySwellHeight sg': 'Sec. Swell Ht (ft) SG',
        'secondarySwellDirection sg': 'Sec. Swell Dir SG',
        'secondarySwellPeriod sg': 'Sec. Swell Per (s) SG',
        'currentDirection sg': 'Current Dir SG',
        'currentSpeed sg': 'Current Spd (mph) SG',
        'waterTemperature sg': 'Water Temp (F) SG',
        'windWaveHeight sg': 'Wind Wave Ht (ft) SG',
        'windWaveDirection sg': 'Wind Wave Dir SG',
        'windWavePeriod sg': 'Wind Wave Per (s) SG',

        # NOAA Model
        'windDirection noaa': 'Wind Dir NOAA',
        'windSpeed noaa': 'Wind Spd (mph) NOAA',
        'gust noaa': 'Gust (mph) NOAA',
        'waveHeight noaa': 'Wave Ht (ft) NOAA',
        'waveDirection noaa': 'Wave Dir NOAA',
        'wavePeriod noaa': 'Wave Per (s) NOAA',
        'swellHeight noaa': 'Swell Ht (ft) NOAA',
        'swellDirection noaa': 'Swell Dir NOAA',
        'swellPeriod noaa': 'Swell Per (s) NOAA',
        'secondarySwellHeight noaa': 'Sec. Swell Ht (ft) NOAA',
        'secondarySwellDirection noaa': 'Sec. Swell Dir NOAA',
        'secondarySwellPeriod noaa': 'Sec. Swell Per (s) NOAA',
        'waterTemperature noaa': 'Water Temp (F) NOAA',
        'windWaveHeight noaa': 'Wind Wave Ht (ft) NOAA',
        'windWaveDirection noaa': 'Wind Wave Dir NOAA',
        'windWavePeriod noaa': 'Wind Wave Per (s) NOAA',

        # METEO Model
        'waveHeight meteo': 'Wave Ht (ft) METEO',
        'waveDirection meteo': 'Wave Dir METEO',
        'wavePeriod meteo': 'Wave Per (s) METEO',
        'swellHeight meteo': 'Swell Ht (ft) METEO',
        'swellDirection meteo': 'Swell Dir METEO',
        'swellPeriod meteo': 'Swell Per (s) METEO',
        'currentDirection meteo': 'Current Dir METEO',
        'currentSpeed meteo': 'Current Spd (mph) METEO',
        'waterTemperature meteo': 'Water Temp (F) METEO',
        'windWaveHeight meteo': 'Wind Wave Ht (ft) METEO',
        'windWaveDirection meteo': 'Wind Wave Dir METEO',
        'windWavePeriod meteo': 'Wind Wave Per (s) METEO',

        # ECMWF Model
        'waveHeight ecmwf': 'Wave Ht (ft) ECMWF',
        'waveDirection ecmwf': 'Wave Dir ECMWF',
        'wavePeriod ecmwf': 'Wave Per (s) ECMWF',
        'windSpeed ecmwf': 'Wind Spd (mph) ECMWF',
        'windDirection ecmwf': 'Wind Dir ECMWF',
        'currentDirection ecmwf': 'Current Dir ECMWF',
        'currentSpeed ecmwf': 'Current Spd (mph) ECMWF',

    }

    df = df.rename(columns=renameorder)

    order = list(renameorder.values())

    columnsorder = [col for col in order if col in df.columns]

    df = df[columnsorder]

    pd.set_option('display.max_rows', None,)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    print(f"\n--- {city} Surf Forecast Printed to CSV Files ---")

    all_renamed_columns = df.columns.tolist()

    models_to_display = ['SG', 'NOAA', 'METEO', 'ECMWF']

    base_columns = ['Time']
    
    for model_id in models_to_display:
        model_specific_cols = [col for col in all_renamed_columns if f" {model_id}" in col]
        current_display_cols = base_columns + [col for col in model_specific_cols if col not in base_columns]
        df_model = df[current_display_cols].copy()
        if not df_model.empty:
            filename = f'SurfReport_{model_id}.csv'
            df_model.to_csv(filename, index=False)
            #print(df_model)
        else:
            print(f"No specific forecast data found for {model_id}.")
        #print("-" * (40 + len(model_id)))

if __name__ == "__main__":
    sys.exit(main())
