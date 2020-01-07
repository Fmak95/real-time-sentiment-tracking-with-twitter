# Real-Time-Sentiment-Tracking-with-Twitter
A real-time web app based on data pipelines using streaming Twitter data, automated sentiment analysis, and MySQL database.

![]("https://imgur.com/kUqihyf")


## Getting Started
### Pre - Installation

I advise that you first create a new python virtual environment before installing the dependencies.

```
pip install -r requirements.txt
```

### Credentials

Create a file called ```credentials.py``` and fill in the contents with your own personal API key and ACCESS token.

```
# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you
ACCESS_TOKEN = "XXXXXXXXX"
ACCESS_TOKEN_SECRET = "XXXXXXXX"
CONSUMER_KEY = "XXXXXXXX"
CONSUMER_SECRET = "XXXXXXXX"
```

### MySQL Database

Download and install mySQL locally on your computer and create a database with the following settings:

```
host = 'localhost'
user = 'root'
password = 'password123'
```
