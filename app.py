import datetime
import mysql.connector
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
from collections import Counter

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children = [
		html.H2('Real-Time Twitter Sentiment Analysis for Analyzing Public Opinion',
			style = {'textAlign': 'center'}),
		html.Div(id='live-update-graph-top'),
		html.Div(id='live-update-graph-bottom'),
		dcc.Interval(
			id = 'interval-component',
			interval = 1 * 60000,
			n_intervals = 0)
	], style = {'padding': '20px'})

def get_data():
	## TO DO: MODULARIZE THE CONNECTION TO DATABASE

	# Connect to the SQL database
	mydb = mysql.connector.connect(
				host = 'localhost',
				user = 'root',
				password = 'password123',
				database = 'twitter_database'
			)

	# Use SQL query to get all tweets from the last 10 minutes
	time_now = datetime.datetime.utcnow()
	time_10mins_before = datetime.timedelta(hours=0,minutes=10)
	time_interval = time_now - time_10mins_before
	query = "SELECT * FROM tweets WHERE created_at >= '{}'".format(time_interval)
	df = pd.read_sql(query, con = mydb)
	return df

##### CALLBACKS #####
@app.callback(Output('live-update-graph-top', 'children'),
	[Input('interval-component', 'n_intervals')])
def update_graph_top(n):
	df = get_data()

	# Assign positive, neutral or negative sentiment to each tweet
	df['sentiment'] = 0
	df.loc[df['compound_score'] >= 0.05, 'sentiment'] = 1
	df.loc[df['compound_score'] <= -0.05, 'sentiment'] = -1

	# Group the dataframe by time and sentiment per 5 second intervals
	result = df.groupby([pd.Grouper(key='created_at', freq='5s'), 'sentiment']).count().unstack(fill_value=0).stack().reset_index()
	# fig = px.line(result, x='created_at',y="id",color='sentiment')

	# Get the top hashtags used
	all_hashes = df.hashtags.values
	all_hashes = [item for item in all_hashes if item is not None]
	all_hashes = [x.lower() for item in all_hashes for x in item.split(',')]

	hashtag_counter = Counter(all_hashes)
	top_hashes = hashtag_counter.most_common()[:10]

	# Create the graphs: Timeseries Graph and Pie Chart
	children = [
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							{
								'x' : result[result['sentiment'] == 0].created_at,
								'y' : result[result['sentiment'] == 0].id,
								'name': 'Neutral',
								'marker': {'color': 'rgb(131, 90, 241)'}
							},
							{
								'x' : result[result['sentiment'] == 1].created_at,
								'y' : result[result['sentiment'] == 1].id,
								'name' : 'Positive',
								'marker': {'color': 'rgb(255, 50, 50)'}
							},
							{
								'x' : result[result['sentiment'] == -1].created_at,
								'y' : result[result['sentiment'] == -1].id,
								'name' : 'Negative',
								'marker': {'color': 'rgb(184, 247, 212)'}
							}
						]
					}
				)], style = {'width': '73%', 'display': 'inline-block', 'padding': '0 0 0 20'}),
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							go.Pie(
									labels = ['Neutral', 'Positive', 'Negative'],
									values = [result[result['sentiment'] == 0].id.sum(),
										result[result['sentiment'] == 1].id.sum(),
										result[result['sentiment'] == -1].id.sum()],
									name = 'pieChart',
									marker_colors = ['rgb(131, 90, 241)','rgb(255, 50, 50)','rgb(184, 247, 212)'],
								)
						]
					}
				)], style = {'width': '27%', 'display': 'inline-block'}),
		html.Div([
			html.H3('Most Used Hashtags in the Last 10 Mins'),
			dcc.Graph(
					figure = {
						'data': [
							go.Bar(
									x = [item[1] for item in top_hashes][::-1],
									y = [item[0] for item in top_hashes][::-1],
									orientation = 'h'
								)
						],
						'layout': {
							'xaxis': {'automargin': True},
							'yaxis': {'automargin': True}
						}
					}
				)], style = {'width': '50%', 'display': 'inline-block'})
	]
	return children


if __name__ == '__main__':
    app.run_server(debug=True)



