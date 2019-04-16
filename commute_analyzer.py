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


def mean_commute_time_plot(morning, evening, beg_range=25, end_range=60):
    """Makes a plot with two buttons to toggle between morning and
       evening commutes. 'beg_range' and 'end_range' toggle the yaxis for
       a clearer plot"""
    # Removing seconds for aesthetics for axis labels
    morning['hour_min'] = morning['hour_min'].astype(str).str[:-3]
    evening['hour_min'] = evening['hour_min'].astype(str).str[:-3]
    traces = []

    updatemenus = [dict(type="buttons",
                        direction='left', pad={'r': 10, 't': 10},
                        showactive=True, x=0,
                        xanchor='left', y=1.25,
                        yanchor='top', buttons=[])]

    PLOT_NAMES = ['Morning', 'Evening']

    for num, df in enumerate([morning, evening]):
        viz = True
        if num == 1:
            viz = False

        traces.append(go.Scatter(x=df['hour_min'],
                                 y=df['duration_in_traffic']['mean'],
                                 line=dict(color='black', width=3, dash='dash'),
                                 name='Average {} Commute'.format(PLOT_NAMES[num]),
                                 visible=viz))

        traces.append(go.Scatter(x=df['hour_min'],
                                 y=df['duration_in_traffic']['perc_95'],
                                 line=dict(color='rgb(202,225,255)'),
                                 name='95th Percentile',
                                 showlegend=False,
                                 visible=viz))

        traces.append(go.Scatter(x=df['hour_min'],
                                 y=df['duration_in_traffic']['perc_5'],
                                 line=dict(color='rgb(202,225,255)'),
                                 name='5th Percentile',
                                 fill='tonexty',
                                 mode='lines',
                                 showlegend=False,
                                 visible=viz))

        updatemenus[0]['buttons'].append(dict(
            label='{} Commute'.format(PLOT_NAMES[num]),
            method='update',
            args=[{'visible':
                   ([True] * 3) + ([False] * 3) if num == 0 else ([False] * 3) + ([True] * 3),
                   'yaxis':dict(title='Minutes in the {}'.format(PLOT_NAMES[num])),
                   }, ]))

    layout = go.Layout(
        updatemenus=list(updatemenus),
        legend=dict(x=0, y=1),
        xaxis=dict(tickangle=45, mirror=True, showline=True),
        yaxis=dict(title='Minutes', range=[beg_range, end_range])

    )

    py.offline.plot({'data': traces, 'layout': layout},
                    filename='mean_commute_times.html',
                    config=dict(modeBarButtonsToRemove=['sendDataToCloud'], showLink=False))


def daily_commute_time_plot(df, yaxismax=100):
    """Plots average daily commute times and returns interactive html.
    Excludes weekends & holidays and plots them as dashed lines"""
    df['date'] = df['time'].dt.date
    daily = df.groupby(['date', 'is_morning'], as_index=False)['duration_in_traffic'].mean()

    # Reindexing to account for weekends/holidays
    timeindex = pd.date_range(start=daily['date'].min(), end=daily['date'].max())

    morning = daily.loc[daily['is_morning'] == 1].drop('is_morning', axis=1).copy()
    morning = morning.set_index('date').reindex(timeindex)

    evening = daily.loc[daily['is_morning'] == 0].drop('is_morning', axis=1).copy()
    evening = evening.set_index('date').reindex(timeindex)

    # Rolling Average of Total Daily Commute Times (excluding weekends/holidays)
    rolling_avg = daily.groupby('date')['duration_in_traffic'].sum().rolling(5).mean()
    rolling_avg = rolling_avg.reindex(timeindex)

    # Individual lines on chart
    trace0 = go.Scatter(x=morning.index,
                        y=morning['duration_in_traffic'].interpolate(),
                        showlegend=False,
                        line=dict(dash='dash', color='orange'),
                        hoverinfo='none')

    trace1 = go.Scatter(x=morning.index,
                        y=morning['duration_in_traffic'],
                        name='Avg. Morning Commute Time',
                        line=dict(color='orange'))

    trace2 = go.Scatter(x=evening.index,
                        y=evening['duration_in_traffic'].interpolate(),
                        showlegend=False,
                        line=dict(dash='dash', color='blue'),
                        hoverinfo='none')

    trace3 = go.Scatter(x=evening.index,
                        y=evening['duration_in_traffic'],
                        name='Avg. Evening Commute Time',
                        line=dict(color='blue'))

    trace4 = go.Scatter(x=rolling_avg.index,
                        y=rolling_avg.interpolate(),
                        hoverinfo='none',
                        showlegend=False,
                        line=dict(color='purple', dash='dash'))

    trace5 = go.Scatter(x=rolling_avg.index,
                        y=rolling_avg.values,
                        name='Total Time (Rolling Avg.)',
                        line=dict(color='purple'))

    layout = go.Layout(legend=dict(x=1, y=1.1, xanchor='right'),
                       yaxis=dict(title='Minutes', range=[0, yaxismax]),
                       xaxis=dict(mirror=True, showline=True))

    py.offline.plot({'data': [trace0, trace1, trace2, trace3, trace4, trace5],
                     'layout': layout},
                    config=dict(modeBarButtonsToRemove=['sendDataToCloud'],
                                showLink=False),
                    filename='./daily_commute.html')


def total_commute_minutes_plot(morning, evening):
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

    trace0 = go.Scatter(x=merged['xlabels'],
                        y=merged['total_avg'],
                        line=dict(color='black', width=3, dash='dash'),
                        name='Avg. Total Commute Time')

    trace1 = go.Scatter(x=merged['xlabels'],
                        y=merged['total_95'],
                        line=dict(color='rgb(140,225,200)'),
                        showlegend=False,
                        name='95th Percentile')

    trace2 = go.Scatter(x=merged['xlabels'],
                        y=merged['total_5'],
                        line=dict(color='rgb(140,225,200)'),
                        name='5th Percentile',
                        fill='tonexty',
                        showlegend=False,
                        mode='lines')

    layout = go.Layout(legend=dict(x=0, y=1.1, xanchor='left'),
                       yaxis=dict(title='Daily Commute Minutes', range=[40, 100]),
                       xaxis=dict(tickangle=45,
                                  mirror=True,
                                  showline=True,
                                  ))

    py.offline.plot({'data': [trace0, trace1, trace2],
                     'layout': layout},
                    config=dict(modeBarButtonsToRemove=['sendDataToCloud'],
                                showLink=False, displayModeBar=False,),

                    filename='./total_commute_minutes.html')
    return merged


def lost_time_plot(merged):
    """Calculates lost time based on average differences with minimum time and plots
    difference on daily and annual basis"""
    minimum_avg_time = merged['total_avg'].min()
    merged['difference_w_min'] = merged['total_avg'] - minimum_avg_time

    trace0 = go.Bar(x=merged['xlabels'],
                    y=merged['difference_w_min'],
                    name='Minutes Lost',
                    marker=dict(color='#B0171F'))

    trace1 = go.Bar(x=merged['xlabels'],
                    y=(merged['difference_w_min'] / (60 * 24)) * 5 * 52,
                    visible=False,
                    name='Days Lost',
                    marker=dict(color='#DC143C'))

    updatemenus = list([
        dict(type="buttons",
             direction='left',
             pad={'r': 10, 't': 10},
             x=0, xanchor='left', y=1.25,
             yanchor='top',
             active=0,
             buttons=list([
                 dict(label='Daily Loss',
                      method='update',
                      args=[{'visible': [True, False]},
                            {'yaxis': {'title': 'Mean <b>Minutes</b> Lost <i>per Day</i>'}}]),
                 dict(label='Annual Loss',
                      method='update',
                      args=[{'visible': [False, True]},
                            {'yaxis': {'title': 'Mean <b>Days</b> Lost <i>per Year</i>'}}])
             ]))])

    layout = go.Layout(xaxis=dict(tickangle=45,
                                  mirror=True,
                                  showline=True,),
                       updatemenus=updatemenus,
                       yaxis=dict(title='Mean <b>Minutes</b> Lost <i>per Day</i>'))

    py.offline.plot({'data': [trace0, trace1],
                     'layout': layout},
                    config=dict(modeBarButtonsToRemove=['sendDataToCloud'],
                                showLink=False, displayModeBar=False,),
                    filename='./lost_time.html')


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
    merged = total_commute_minutes_plot(morning, evening)
    mean_commute_time_plot(morning, evening)
    daily_commute_time_plot(df)
    lost_time_plot(merged)
    print_statistics(merged, morning, evening)


if __name__ == '__main__':
    main()
