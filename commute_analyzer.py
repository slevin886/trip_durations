"""Takes in google API commute data and returns statistics and figures"""

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
import re
import datetime
from plots import (mean_commute_time_plot, daily_commute_time_plot, lost_time_plot,
                   commute_distance_variation_plot, total_commute_minutes_plot)

# TODO: add assertions/tests, more flexibility for when it might be implemented in the future, additional statistics

HOURS_OF_INTEREST = [6, 7, 8, 9, 15, 16, 17, 18]
HOLIDAYS = USFederalHolidayCalendar().holidays('2018', '2020')
KM_2_MILES = 1.609


def time_date_adjustments(csv_loc='./commute_info.csv'):
    """Adjusting for daylight savings, making eastern standard time, dropping holidays.
       Make sure you adjust the daylightsavings conditions based on to adjust for dates of
       use"""
    df = pd.read_csv(csv_loc)
    df['time'] = pd.to_datetime(df['time']) - pd.Timedelta(5, unit='h')
    df['time'] = df.time.dt.round('1min')
    # Adjusting or daylight savings
    daylight = (df['time'] < datetime.date(2018, 11, 4))
    df.loc[daylight, 'time'] = df.loc[daylight, 'time'] + pd.Timedelta(1, unit='h')
    # Ensuring there are no times outside of HOURS_OF_INTEREST
    df = df.drop(df.loc[~df['time'].dt.hour.isin(HOURS_OF_INTEREST)].index)
    df.reset_index(drop=True, inplace=True)
    # Dropping holidays
    df = df.drop(df.loc[df['time'].dt.date.isin(HOLIDAYS)].index)
    df.reset_index(drop=True, inplace=True)
    # Adding Morning/Evening Dummy Variable
    df['is_morning'] = df.time.apply(lambda x: 1 if x.hour < 11 else 0)
    return df


def duration_clean(mins):
    """Eliminates text from duration descriptions and changes hours to minutes"""
    if 'h' in mins:
        vals = re.findall(r'\d+', mins)
        # if more than hour, returns two numbers because of google's format
        return int(vals[0]) * 60 + int(vals[1])
    else:
        return int(re.search(r'\d+', mins).group())


def distance_conversion(dist):
    """Cleans distance column to remove text and convert to miles"""
    try:
        clean_dist = float(dist.replace('km', ''))
    except:
        print("Unexpected distance value encountered")
        return
    return round(clean_dist / KM_2_MILES, 1)


def remove_weekends(df):
    """Removes Weekends from Commute Consideration"""
    df['is_weekday'] = df['time'].apply(lambda x: 1 if x.dayofweek < 5 else 0)
    df = df.drop(df.loc[df['is_weekday'] == 0].index)
    df.reset_index(drop=True, inplace=True)
    df = df.drop(['is_weekday'], axis=1)
    return df


def perc_95(x):
    return x.quantile(0.95)


def perc_5(x):
    return x.quantile(0.05)


def time_aggregator(df):
    """Groups commute times by 5 minute increment and returns time stats"""
    df['hour_min'] = df['time'].dt.time
    calculations = {'distance': 'nunique',
                    'duration_in_traffic': ['mean', 'max', 'min', 'median', perc_95, perc_5]}
    final = []
    for num, time in enumerate(['morning', 'evening']):
        newdf = df.loc[df['is_morning'] == num]
        assert newdf.origin.value_counts().shape[0] == 1, 'Multiple origins in data'
        avgdf = newdf.groupby('hour_min', as_index=False).agg(calculations)
        final.append(avgdf)
    return final[0], final[1]


def merge_morning_evening_data(morning, evening):
    """Merges morning and evening data, returns the merged data set, and plots
    the 95% intervals for total commute time given departure times at 8 hour spreads"""
    morning['merge'] = morning['hour_min'].astype(str).str[:5].str.replace(':', '.').astype(float) + 8
    evening['merge'] = evening['hour_min'].astype(str).str[:5].str.replace(':', '.').astype(float)
    merged = pd.merge(morning, evening, on='merge')
    merged['total_avg'] = merged['duration_in_traffic_x']['mean'] + merged['duration_in_traffic_y']['mean']
    merged['total_95'] = merged['duration_in_traffic_x']['perc_95'] + merged['duration_in_traffic_y']['perc_95']
    merged['total_5'] = merged['duration_in_traffic_x']['perc_5'] + merged['duration_in_traffic_y']['perc_5']
    merged['total_median'] = merged['duration_in_traffic_x']['median'] + merged['duration_in_traffic_y']['median']
    merged['xlabels'] = merged['hour_min_x'].astype(str).str[:-3] + '-' + merged['hour_min_y'].astype(str).str[:-3]
    return merged


def print_statistics(merged, morning, evening, metric='mean'):
    # Best/Worst Times
    worst_morn = morning.loc[morning['duration_in_traffic'][metric] == morning['duration_in_traffic'][metric].max()]
    best_morn = morning.loc[morning['duration_in_traffic'][metric] == morning['duration_in_traffic'][metric].min()]
    worst_evening = evening.loc[evening['duration_in_traffic'][metric] == evening['duration_in_traffic'][metric].max()]
    best_evening = evening.loc[evening['duration_in_traffic'][metric] == evening['duration_in_traffic'][metric].min()]
    print('**BEST & WORST AVERAGE DEPARTURE TIMES [DEPARTURE] [MINUTES]**')
    print('**MORNING**')
    print('Best: ', best_morn['hour_min'].tolist(), best_morn['duration_in_traffic'][metric].tolist())
    print('Worst: ', worst_morn['hour_min'].tolist(), worst_morn['duration_in_traffic'][metric].tolist())
    print('**EVENING**')
    print('Best: ', best_evening['hour_min'].tolist(), best_evening['duration_in_traffic'][metric].tolist())
    print('Worst: ', worst_evening['hour_min'].tolist(), worst_evening['duration_in_traffic'][metric].tolist())
    print('\n**BEST 8 HOUR INTERVAL DEPARTURES**')
    median_min = merged.loc[merged['total_median'] == merged['total_median'].min()]
    avg_min = merged.loc[merged['total_avg'] == merged['total_avg'].min()]
    print('Minimum Time (Median): ', median_min['xlabels'].tolist(), median_min['total_median'].tolist())
    print('Minimum Time (Avg): ', median_min['xlabels'].tolist(), median_min['total_avg'].tolist())


def main():
    df = time_date_adjustments()
    df['duration_in_traffic'] = df['duration_in_traffic'].apply(duration_clean)
    df['distance'] = df['distance'].apply(distance_conversion)
    df = remove_weekends(df)
    evening, morning = time_aggregator(df)
    merged = merge_morning_evening_data(morning, evening)
    mean_commute_time_plot(morning, evening)
    daily_commute_time_plot(df)
    commute_distance_variation_plot(df)
    total_commute_minutes_plot(merged)
    lost_time_plot(merged)
    print_statistics(merged, morning, evening)


if __name__ == '__main__':
    main()
