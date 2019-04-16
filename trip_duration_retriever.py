"""This is a script to collect the duration of a commute from google maps"""

import pandas as pd
import requests
import datetime
import os.path
from google_api import PASSWORD

# Replace with the coordinates of your own home and work
HOME = '42.339165, -71.152060'
WORK = '42.504682, -71.244258'
# Replace PASSWORD with your own Google API password
PWORD = PASSWORD
PATH = './commute_info.csv'


def commute_time_calculator(home, work, api_key):
    """Pings google API and returns commute information.
    The coordinate for start and end should be 'latitude, longitude'
    as one unified string each, hours for direction are UTC for commute.
    Maps API defaults to 'best guess' for traffic duration, a combination of historical
    averages and live traffic information."""
    time_now = datetime.datetime.now()
    if time_now.hour < 18:
        start_coord = home
        end_coord = work
    else:
        start_coord = work
        end_coord = home
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={}&destinations={}&mode=driving&language=en-EN&departure_time=now&key={}".format(start_coord, end_coord, api_key)
    try:
        duration = requests.get(url)
    except:
        print "There is something wrong with the URL or your coordinates"
    result = duration.json()
    commute = {}
    commute['distance'] = result['rows'][0]['elements'][0]['distance']['text']
    commute['duration_in_traffic'] = result['rows'][0]['elements'][0]['duration_in_traffic']['text']
    commute['destination'] = result['destination_addresses']
    commute['origin'] = result['origin_addresses']
    commute['time'] = time_now
    df = pd.DataFrame(commute, index=[0])
    return df


def csv_writer(df, path):
    """Feed the path/name you want to CSV to save to as well as the
    dataframe from your new commute_time_calculator trip"""
    if os.path.exists(path):
        with open(path, 'a') as f:
            df.to_csv(f, header=False, index=False)
            print "Successfully appended to CSV"
    else:
        df.to_csv(path, index=False)
        print "Successfully created CSV"


def main():
    frame = commute_time_calculator(HOME, WORK, PWORD)
    csv_writer(frame, PATH)
    print "Successfully Obtained Trip Info!!"


if __name__ == "__main__":
    print "Starting trip duration retrieval"
    main()
