import dash
from dash import html
from dash import dcc

dash.register_page(__name__, path='/')

layout = dcc.Markdown('''

#### DASH Framework for energy usage

##### Purpose

This is a very basic attempt at using Dash to represent household power and gas usage based on hourly usage data. This project was triggered by receiving a powerbill 40-50% higher than expected. 

The purpose of the dashboards was originally to get a better understanding of the pattern of power usage, and the appliances that were responsible for the increased draw. Once the reasons were understood, the ongoing use of the dashboard is to monitor the patterns of usage and ensure things stay under control.

##### Data sources 
The energy usage data has been downloaded as daily csv files with hourly usage totals from the [Genesis Energy website](https://www.genesisenergy.co.nz) and subsequently stored in a parquet file. There needs to be something scheduled to review the download folder and update the parquet file. At the moment, updates occur by running `main.py`.

Note: There is be a webservice that might be used for this, but accessing and understanding it is still a work in progress. 

Air Temperature data has also been pulled from [Taranaki Regional Council's](https://www.trc.govt.nz/) [environmental data service](https://extranet.trc.govt.nz/getdata/boo.hts). This data is pulled as 10 minute time-value pairs and stored in a parquet file before plotting on the dashboard.

##### Dash framework
A combination of ChatGPT and Gemini prompts have been used in the construction of the dashboards. It made getting a working framework up and running much quicker.

Inspiration was also taken from @harrysdatajournery channel on youtube. He had a video showing a [multipage dashboard](https://www.youtube.com/watch?v=YU7bCEcsBK8). With the original four dashboards generated for this project, these dashboards are now combined into one `flask_app.py` file.

![dashboard](https://github.com/seanlhodges/energy_consumption/blob/main/dashboard-heatmaps-barplots.png)

##### Future work

1. Get this code running on a webserver. DONE - [pythonanywhere.com](https://www.pythonanywhere.com)
2. Create automated tasks to check for new data, run `main.py` to update the datastores, and push changes to github (`pip install GitPython`)
3. Create scheduled task on pythonanywhere to pull changes from github and refresh the dashboard data.

##### Current Process

1. Download daily files for hourly gas and electricity usage. These data are downloaded separately, and files are renamed to identify which is gas and which is electricity.
2. Downloaded files are copied to a data folder within the python working directory.
3. Within the python IDE (VSCode), `main.py` is run to update the datastores used by the dashboards.
4. With the data updated, changes are committed in git, and pushed to the github repo.
5. From a console in pythonanywhere, `git pull origin main` is run within the working directory
6. The webservice is reloaded on pythonanywhere.
7. Dashboards are reviewed 
''')


# layout = html.Div([
#     html.H2('Purpose'),
#     html.P('''
#              This is a very basic attempt at using Dash to represent household power and 
#              gas usage based on hourly usage data. This project was triggered by receiving 
#              a powerbill 40-50% higher than expected.
#              '''),
#     html.P('''
#              The purpose of the dashboards was originally to get a better understanding of the 
#              pattern of power usage, and the appliances that were responsible for the increased 
#              draw. Once the reasons were understood, the ongoing use of the dashboard is to 
#              monitor the patterns of usage and ensure things stay under control.
#              '''),
# ])