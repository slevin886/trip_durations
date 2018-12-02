# Route Optimization

The 'trip_retriever' script is currently running on an EC2 collecting data (duration & route) every 5 minutes of my morning and evening commutes using the Google Maps API. I plan to identify the optimal commute given an 8 hour workday and varying parameters (tolerance for route variation, flexibility for morning departure time, etc.). The script began running on November 1st, 2018 and I will let it run for at least 2 months prior to beginning a preliminary analytic process. 

The jupyter notebook provides a script for the initial exploratory analysis and visualizations. Below is a preliminary visualization of minute-by-minute duration for the morning commute by day (comparing weekday (blue) & weekend (red) trips). As a result, I have extended the cronjob to collect data until 10am to see the trip duration's decline and will eliminate holidays (the shorter duration weekday trips are a result of the Thanksgiving holiday and bias the mean times downward).  

<p align="center">
  <img src="https://github.com/slevin886/trip_durations/blob/master/images/prelim_image.png" height="360" width="600">
</p>

