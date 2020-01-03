import credentials
import tweepy
import mysql.connector
from tweepy.streaming import StreamListener
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import pdb
import re

class TwitterAnalyzer():

	def store_hashtags(self, text):
		matches = re.findall('#(\w+)', text)

		if len(matches) > 0:
			hashtags = [match for match in matches]
			return hashtags
		else:
			return None

	def clean_text(self, text):
		#Remove URLs
		clean_text = re.sub(r'http\S+', '', text)

		#Remove Username Handles
		clean_text = re.sub('@[^\s]+', '', clean_text)

		#Remove Hashtags
		clean_text = re.sub('#[^\s]+', '', clean_text)

		#Replace newline with space
		clean_text = clean_text.replace('\n', ' ')

		return clean_text.strip()

	def get_sentiment_score(self, text):
		analyzer = SentimentIntensityAnalyzer()
		return analyzer.polarity_scores(text)

class DatabaseManager():

	def __init__(self, host, password, user = "root", database = None):
		self.mydb = mysql.connector.connect(
				host = host,
				user = user,
				password = password,
				database = database
			)
		self.mycursor = self.mydb.cursor()

		print(self.mydb)

	def create_database(self, database_name = "twitter_database"): 
		self.mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(database_name))

	def create_table(self, table_name = "tweets"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
			id VARCHAR(255),\
			created_at DATETIME,\
			author VARCHAR(255),\
			text LONGTEXT,\
			retweet_count INT,\
			favorite_count INT,\
			neg_score FLOAT,\
			neu_score FLOAT,\
			pos_score FLOAT,\
			compound_score FLOAT,\
			hashtags VARCHAR(255),\
			search_words VARCHAR(255))".format(table_name))

	#Emojis require that you use utf8mb4 encoding instead of the traditional utf8
	def alter_table_for_emojis(self, database_name = "twitter_database", table_name = "tweets"):
		self.mycursor.execute('SET NAMES utf8mb4')
		self.mycursor.execute("SET CHARACTER SET utf8mb4")
		self.mycursor.execute("SET character_set_connection=utf8mb4")


	def insert_data(self, id, created_at, author, text, retweet_count, favorite_count,
		neg_score, neu_score, pos_score, compound_score, hashtags, search_words, table_name="tweets"):
		sql = """
			INSERT INTO {} (id, created_at, author, text, retweet_count, favorite_count, neg_score, neu_score, pos_score, compound_score, hashtags, search_words)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		""".format(table_name)

		val = (id, created_at, author, text, retweet_count, favorite_count, neg_score,
			neu_score, pos_score, compound_score, hashtags, search_words)

		self.mycursor.execute(sql, val)
		self.mydb.commit()

	# Method for deleting the database in case of errors, used for debugging
	def delete_database(self):
		sql = "DROP DATABASE twitter_database"
		self.mycursor.execute(sql)

	#Method that contains all of my debugging code, should delete later
	def debug(self):

		print("DATABASES ARE BELOW: ")
		self.mycursor.execute("SHOW DATABASES")
		for db in self.mycursor:
			print(db)

		self.mycursor.execute("SELECT * FROM tweets")
		myresult = self.mycursor.fetchall()

		print("DATA: ")
		for row in myresult:
			print(row)

class TwitterListener(StreamListener):

	def __init__(self, num_tweets_to_grab):
		super(TwitterListener, self).__init__()
		self.counter = 0
		self.num_tweets_to_grab = num_tweets_to_grab
		self.twitter_analyzer = TwitterAnalyzer()
		self.database_manager = DatabaseManager("localhost", "password123")

		#Create database and table on initialization of TwitterListener
		self.database_manager.create_database()

		#Reinitialize database manager to connect with the database we just created
		self.database_manager = DatabaseManager("localhost", "password123", database="twitter_database")

		self.database_manager.create_table()
		self.database_manager.alter_table_for_emojis()

	def on_status(self, status):

		if self.counter == self.num_tweets_to_grab:
			return False

		#Avoid retweeted info
		if 'retweeted_status' in dir(status):
			return True

		# # # Getting Useful Attributes form Each Tweet # # #

		#Twitter recently increased max character count for tweets... 
		#therefore the new tweets with more characters have the full text in 'extended_tweet'
		#old tweets full text can be found in 'text'
		if 'extended_tweet' in dir(status):
			text = status.extended_tweet['full_text']

		else:
			text = status.text

		id = status.id_str #Str: This id will be used as primary key in SQL database
		created_at = status.created_at #Datetime: Specifying when tweet was created
		retweet_count = status.retweet_count #Int: number of times tweet was retweeted
		favorite_count = status.favorite_count #Int: number of times tweet was favorited
		author = status.user.screen_name #Str: username of the tweet's author

		# Store hashtags as comma seperated string
		hashtags = self.twitter_analyzer.store_hashtags(text)

		if hashtags:
			hashtags = ','.join(hashtags)

		# Clean text: Remove URLS, Hashtags and Username Handles
		text = self.twitter_analyzer.clean_text(text)

		#Get the sentiment score using VADER
		sentiment_score = self.twitter_analyzer.get_sentiment_score(text)
		neg_score = sentiment_score['neg']
		neu_score = sentiment_score['neu']
		pos_score = sentiment_score['pos']
		compound_score = sentiment_score['compound']

		### Print Statements for DEBUGGING ###
		print("Text: " + text)
		print("Score: {}".format(sentiment_score))
		# print("Hashtags: {}".format(hashtags))

		# # # Adding the Twitter Data into mySQL Database # # #
		self.database_manager.insert_data(id, created_at, author, text, retweet_count, favorite_count,
		neg_score, neu_score, pos_score, compound_score, hashtags, search_words[0])

		self.database_manager.debug()
		self.counter += 1

	def on_error(self, error_code):
		# Twitter API has rate limits, stop scraping data when warning is shown
		if error_code == 420:
			return False

class TwitterStreamer():
	def stream_tweets(self, search_words, num_tweets_to_grab = 4000):

		#Handles Twitter Authentication and Connects to Twitter Streaming API
		listener = TwitterListener(num_tweets_to_grab)
		auth = tweepy.OAuthHandler(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET)
		auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)
		stream = tweepy.Stream(auth, listener, tweet_mode = "extended")

		# Filter Twitter Streams to capture data by the keywords:
		stream.filter(track = search_words, languages=["en"])

if __name__ == '__main__':
	search_words = ["Trump"]
	twitter_streamer = TwitterStreamer()
	twitter_streamer.stream_tweets(search_words)

