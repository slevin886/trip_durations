# Commute Route Optimization

## Summary
This project enables the user to collect data on a morning & evening commute (using the Google Maps' API) over time and produce interactive visualizations and summary data to determine optimal departure times (i.e. minimizing travel time- although distance is also collected, based on google's 'optimal' route at the time the API is hit). Tested with Python 3.7, but should be good to go with any python 3 version.

## How to Use

Modify 'trip_duration_retriever.py' with your home & office coordinates as well as your google API key (which you can get [here](https://developers.google.com/api-client-library/python/guide/aaa_apikeys)). You should then set this on a cronjob (ideally on an AWS EC2 or something similar, but can be on your local computer- script to come to help with this). You should collect data for as long as possible to account for seasonal traffic variations. A '.csv' file will be created in the project directory (once) and appended to each time you run the script (which you should run every ~5 minutes during the hours you might potentially commute).

Once you have collected (at least a week or two of) data, you can then run 'commute_analyzer.py' which will produce five interactive html visualizations (saved to your project directory as .html files) to help you analyze your commute as well as print summary statistics to the console.

## Sample Graphics

This graph shows the average, 5th, and 95th percentile commute times (in minutes) at the times you collected data for. Using the buttons at the top of the figure, you can toggle between morning/evening commute.

<p align="left">
  <img src="https://github.com/slevin886/trip_durations/blob/master/images/commute_times.png" height="420" width="560">
</p>

This graph shows you the seasonal variations in morning, evening, and total commute times.

<p align="left">
  <img src="https://github.com/slevin886/trip_durations/blob/master/images/daily_commutes.png" height="420" width="560">
</p>

This graph with subplots shows the average route miles of your 'optimal' route for both morning/evening commutes as well as the number of differnet optimal routes at each of the times collected.

<p align="left">
  <img src="https://github.com/slevin886/trip_durations/blob/master/images/commute_distances.png" height="420" width="560">
</p>
