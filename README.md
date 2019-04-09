# Route Optimization

I used the 'trip_retriever' script as a cron job on an EC2 to collect data (duration & route) every 5 minutes for my morning and evening commutes using the Google Maps API (over 96 days). 'commute_analyzer.py' can be run from the command line to (currently) clean the data (adjust for daylight savings, etc.) and produce two interactive html plots showing mean commute duration every 5 minutes (w/ 5th & 95th percentiles to illustrate variation).

To use the code, a few small changes would be necessary (for example, changing the coordinates in 'trip_retriever', getting a google api key)- I have tried to annotate where these changes would be needed in the code. This project is ongoing.


