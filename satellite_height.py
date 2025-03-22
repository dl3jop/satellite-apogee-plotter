#!/usr/bin/ python3

# Joshua, DL3JOP, 2025

# Get current TLEs and plot satellite apogee of time.

# This is a quick'n'dirty script to play around with. Do not expect proper error handling or optimization 

# import necessary libraries
import matplotlib.pyplot as plt
from skyfield.api import load, EarthSatellite, Topos, wgs84, Distance
from datetime import datetime, timedelta, timezone
import requests
import os

# Fetch TLE if there is no file already in the current folder
def fetch_tle(satellite_name, tle_file="tle.txt"):
    if os.path.exists(tle_file):
        with open(tle_file, "r") as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if satellite_name in lines[i]:
                    return lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()
    
    # Fetch from Celestrak if file is not found
    url = f'https://www.celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
    response = requests.get(url)
    lines = response.text.split('\n')
    with open(tle_file, "w") as file:
        file.write(response.text)
    
    for i in range(len(lines)):
        if satellite_name in lines[i]:
            return lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()
    
    return None

def compute_apogee_over_time(tle_lines, days=180, observer_lat=0, observer_lon=0, observer_alt=0):
    # Compute the maximum apogee height when the satellite is visible to the observer within a 24-hour time frame over a duration of one year.
    ts = load.timescale()
    satellite = EarthSatellite(tle_lines[1], tle_lines[2], tle_lines[0], ts)
    observer = wgs84.latlon(observer_lat,observer_lon,observer_alt)

    start_date = datetime.now(timezone.utc)
    times = [start_date + timedelta(days=i) for i in range(days)]
    heights = []
    
    for time in times:
        daily_heights = []
        # timespan: one day
        t0 = ts.utc(time.year, time.month, time.day)
        t1 = ts.utc(time.year, time.month, time.day+1)
        # find all events: for amateurradio satellite DX contacts, only AOS and LOS are used
        t, events = satellite.find_events(observer, t0, t1, altitude_degrees=0.0)
        for ti, event in zip(t, events):
            if event == 0 or event == 2: #AOS or LOS, no TCA
                # Find apogee at AOS/LOS
                subpoint = wgs84.subpoint(satellite.at(ti))
                #print("LOS/AOS at: "+ti.utc_strftime('%Y %b %d %H:%M:%S') + " | Height  " + str(subpoint.elevation.km))
                daily_heights.append(subpoint.elevation.km)
        heights.append(max(daily_heights) if daily_heights else 0)  # Avoid empty max error
    
    return times, heights

def plot_apogee(times, heights, satellite_name, days):
    # Plot the apogee height over time.
    plt.figure(figsize=(10, 5))
    plt.plot(times, heights, label=f'{satellite_name} Apogee height')
    plt.xlabel('Date')
    plt.ylabel('Apogee height (km)')
    plt.title(f'Apogee height of {satellite_name} over {days} days')
    plt.legend()
    plt.grid()
    plt.show()

if __name__ == "__main__":
    satellite_name = "NOAA 15" #"RADFXSAT (FOX-1B)"#"FUNCUBE-1 (AO-73)"#"EYESAT A (AO-27)" # "OSCAR 7 (AO-7)"#"RS-44 & BREEZE-KM R/B"  # Example satellite
    observer_lat = 49.24
    observer_lon = 7.0
    observer_alt = 400
    
    days = 180
    
    tle_data = fetch_tle(satellite_name)
    
    if tle_data:
        times, heights = compute_apogee_over_time(tle_data,days, observer_lat=observer_lat, observer_lon=observer_lon, observer_alt=observer_alt)
        plot_apogee(times, heights, satellite_name, days)
    else:
        print("Satellite not found in TLE database.")
