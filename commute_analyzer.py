"""Takes in google API commute data and returns statistics and figures"""

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
import plotly as py
import plotly.graph_objs as go
import re
import datetime

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
    """Groups commute times by ho"""
    df['hour_min'] = df['time'].dt.time
    calculations = {'distance': 'nunique',
                    'duration_in_traffic': ['mean', 'max', 'min', perc_95, perc_5]}
    final = []
    for num, time in enumerate(['morning', 'evening']):
        newdf = df.loc[df['is_morning'] == num]
        assert newdf.origin.value_counts().shape[0] == 1, 'Multiple origins in data'
        avgdf = newdf.groupby('hour_min', as_index=False).agg(calculations)
        final.append(avgdf)
    return final[0], final[1]


def plot_maker(df, which_commute):
    MAX_TIME = df['duration_in_traffic']['perc_95'].max()

    MIN_TIME = df['duration_in_traffic']['perc_5'].min()

    trace0 = go.Scatter(x=df['hour_min'],
                        y=df['duration_in_traffic']['mean'],
                        line=dict(color='black', width=3),
                        name='Average Time'
                        )

    trace1 = go.Scatter(x=df['hour_min'],
                        y=df['duration_in_traffic']['perc_95'],
                        line=dict(color='orange'),
                        name='95th Percentile',
                        showlegend=False
                        )

    trace2 = go.Scatter(x=df['hour_min'],
                        y=df['duration_in_traffic']['perc_5'],
                        line=dict(color='orange'),
                        name='5th Percentile',
                        fill='tonexty',
                        mode='lines',
                        showlegend=False)

    data = [trace0, trace1, trace2]

    layout = go.Layout(title='Average Commute Time',
                       xaxis=dict(title='Time of Day'),
                       yaxis=dict(title='Minutes', range=[MIN_TIME - 5, MAX_TIME + 5]))

    fig = go.Figure(data=data, layout=layout)

    py.offline.plot(fig, filename='{}.html'.format(which_commute),
                    config=dict(modeBarButtonsToRemove=['sendDataToCloud'],
                                  showLink=False))


def main():
    df = time_date_adjustments()
    df['duration_in_traffic'] = df['duration_in_traffic'].apply(duration_clean)
    df['distance'] = df['distance'].apply(distance_conversion)
    df = remove_weekends(df)
    evening, morning = time_aggregator(df)
    plot_maker(evening, 'evening')
    plot_maker(morning, 'morning')


if __name__ == '__main__':
    main()
