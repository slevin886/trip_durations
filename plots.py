import plotly.graph_objs as go
import pandas as pd
import plotly as py


def plot_data_to_html(func):
    """
    Takes plot data and title from plot functions and produces interactive html
    :param func: plot function
    :return: data ready for plot with y-axis values converted
    """
    def wrapper_plot_data_to_html(*args, **kwargs):
        plot_data, filename = func(*args, **kwargs)
        py.offline.plot(plot_data, config=dict(modeBarButtonsToRemove=['sendDataToCloud'], showLink=False,
                                               displayModeBar=False,),
                        filename=filename)
        return
    return wrapper_plot_data_to_html


@plot_data_to_html
def mean_commute_time_plot(morning, evening, beg_range=25, end_range=60):
    """Makes a plot with two buttons to toggle between morning and
       evening commutes. 'beg_range' and 'end_range' toggle the yaxis for
       a clearer plot"""
    # Removing seconds for aesthetics for axis labels
    morning['hour_min'] = morning['hour_min'].astype(str).str[:-3]
    evening['hour_min'] = evening['hour_min'].astype(str).str[:-3]
    data = []

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

        data.append(go.Scatter(x=df['hour_min'],
                                 y=df['duration_in_traffic']['mean'],
                                 line=dict(color='black', width=3, dash='dash'),
                                 name='Average {} Commute'.format(PLOT_NAMES[num]),
                                 visible=viz))

        data.append(go.Scatter(x=df['hour_min'],
                                 y=df['duration_in_traffic']['perc_95'],
                                 line=dict(color='rgb(202,225,255)'),
                                 name='95th Percentile',
                                 showlegend=False,
                                 visible=viz))

        data.append(go.Scatter(x=df['hour_min'],
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

    layout = go.Layout(updatemenus=list(updatemenus), legend=dict(x=0, y=1),
                       xaxis=dict(tickangle=45, mirror=True, showline=True),
                       yaxis=dict(title='Minutes', range=[beg_range, end_range]))
    fig = go.Figure(data=data, layout=layout)
    return fig, 'mean_commute_times.html'


@plot_data_to_html
def daily_commute_time_plot(df, yaxismax=100):
    """Plots average daily commute times and returns interactive html.
    Excludes weekends & holidays and plots them as dashed lines"""
    df['date'] = df['time'].dt.date
    daily = df.groupby(['date', 'is_morning'], as_index=False)['duration_in_traffic'].mean()

    # Reindexing to account for weekends/holidays
    time_index = pd.date_range(start=daily['date'].min(), end=daily['date'].max())

    morning = daily.loc[daily['is_morning'] == 1].drop('is_morning', axis=1).copy()
    morning = morning.set_index('date').reindex(time_index)

    evening = daily.loc[daily['is_morning'] == 0].drop('is_morning', axis=1).copy()
    evening = evening.set_index('date').reindex(time_index)

    # Rolling Average of Total Daily Commute Times (excluding weekends/holidays)
    rolling_avg = daily.groupby('date')['duration_in_traffic'].sum().rolling(5).mean()
    rolling_avg = rolling_avg.reindex(time_index)

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
    fig = go.Figure(data=[trace0, trace1, trace2, trace3, trace4, trace5], layout=layout)
    return fig, './daily_commute.html'


@plot_data_to_html
def lost_time_plot(merged):
    """
    Calculates lost time based on average differences with minimum time and plots
    difference on daily and annual basis
    :param merged: A dataframe looking at 8 hour intervals of commute data
    :return: Data ready for plot, and filename
    """
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
    fig = go.Figure(data=[trace0, trace1], layout=layout)
    return fig, './lost_time.html'


@plot_data_to_html
def commute_distance_variation_plot(df):
    """
    Creates plot with 4 subplots of commute distance variation for evening/morning commutes.
    :param df: Data Frame of Cleaned Commute Data
    :return: Plot data of distance variations with 4 subplots
    """
    frames = []
    # 0 is evening, 1 is morning
    for i in range(2):
        commute = df.loc[df['is_morning'] == i].copy()
        commute = commute.groupby('hour_min').agg({'distance': ['mean', 'unique']})
        commute.columns = commute.columns.droplevel()
        commute['num_commutes'] = commute['unique'].apply(len)
        frames.append(commute)

    trace1 = go.Scatter(x=frames[1].index.astype(str).str[:-3],
                        y=frames[1]['mean'],
                        showlegend=False,
                        name='Avg. Miles'
                        )

    trace2 = go.Scatter(x=frames[0].index.astype(str).str[:-3],
                        y=frames[0]['mean'],
                        showlegend=False,
                        name='Avg. Miles')

    trace3 = go.Bar(x=frames[1].index.astype(str).str[:-3],
                    y=frames[1]['num_commutes'],
                    showlegend=False,
                    name='# of Routes',
                    marker=dict(color='blue')
                    )

    trace4 = go.Bar(x=frames[0].index.astype(str).str[:-3],
                    y=frames[0]['num_commutes'],
                    showlegend=False,
                    name='# of Routes',
                    marker=dict(color='orange')
                    )

    fig = py.tools.make_subplots(rows=2, cols=2, subplot_titles=('<b>Morning</b> Avg. Route Miles',
                                                                 '<b>Evening</b> Avg. Route Miles',
                                                                 '<b>Morning</b> # of Optimal Routes',
                                                                 '<b>Evening</b> # of Optimal Routes'))
    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 1, 2)
    fig.append_trace(trace3, 2, 1)
    fig.append_trace(trace4, 2, 2)
    fig['layout'].update(title='Variation in <b>Route</b><br><i>that minimizes commute time</i>')
    fig['layout']['yaxis1'].update(dict(range=[15, 25], title='Miles'))
    fig['layout']['yaxis2'].update(dict(range=[15, 25]))
    fig['layout']['yaxis3'].update(dict(range=[0, 25], title='Count'))
    fig['layout']['yaxis4'].update(dict(range=[0, 25]))
    for ind in range(4):
        fig['layout']['annotations'][ind].update(dict(font=dict(size=12)))
    return fig, 'route_variation.html'


@plot_data_to_html
def total_commute_minutes_plot(merged):
    """Plots the 95% intervals for total commute time given departure times at 8 hour spreads"""
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
    fig = go.Figure(data=[trace0, trace1, trace2], layout=layout)
    return fig, './total_commute_minutes.html'
