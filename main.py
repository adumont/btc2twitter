import os
import random
import re
import sys
import twitter
import requests
import datetime
import redis

# Load Heroku Config Variables (https://devcenter.heroku.com/articles/config-vars)
MY_CONSUMER_KEY = os.environ['MY_CONSUMER_KEY']
MY_CONSUMER_SECRET = os.environ['MY_CONSUMER_SECRET']
MY_ACCESS_TOKEN_KEY = os.environ['MY_ACCESS_TOKEN_KEY']
MY_ACCESS_TOKEN_SECRET = os.environ['MY_ACCESS_TOKEN_SECRET']
TWEET_ACCOUNT = os.environ['TWEET_ACCOUNT']
REDIS_URL = os.getenv('REDISTOGO_URL')

FREQ = int(os.getenv('FREQ', 8))
DEBUG = os.getenv('DEBUG', False) == "True"

# some API Parameters for user_timeline
INCLUDE_RTS = os.getenv('INCLUDE_RTS', True) == "True"
EXCLUDE_REPLIES = os.getenv('EXCLUDE_REPLIES', False) == "True"

redis = redis.from_url(REDIS_URL)

# build a (connected) Twitter API object
def connect():
    api = twitter.Api(consumer_key=MY_CONSUMER_KEY,
                          consumer_secret=MY_CONSUMER_SECRET,
                          access_token_key=MY_ACCESS_TOKEN_KEY,
                          access_token_secret=MY_ACCESS_TOKEN_SECRET)
    return api

# post tweet to twitter (or console)
def post_tweet(api, debug, ebook_tweet):
    if debug == True:
        print "DEBUG: " + ebook_tweet
    else:
        status = api.PostUpdate(ebook_tweet)
        print status.text.encode('utf-8')        

def get_old_bitcoin_price():
   return redis.get('last_price')

def get_bitcoin_price():
   a = requests.get('https://api.coindesk.com/v1/bpi/currentprice/EUR.json').json()
   return a['bpi']['EUR']['rate_float']
    
def main(argv):
    debug = DEBUG
    
    # determine if we run or exit
    if FREQ>0 and debug==False:
        now = datetime.datetime.now().hour % FREQ
    else:
        now = 0

    if now > 0:
        print str(now) + " No, sorry, not this time."
        sys.exit()

    # connect to API if necessary
    if debug == False:
        api = connect()
    else:
        api = None

    price_now = float( get_bitcoin_price() )
    price_old = get_old_bitcoin_price()
    if price_old == None:
        price_old = price_now

    price_old = float( price_old )

    diff = (price_now/price_old -1)*100

    print "Old : " + str(price_old)
    print "Now : " + str(price_now)
    print "Diff: " + str(diff) + "%"

    tweet = "El precio de 1 btc es " + str(price_now) + " EUR"

    if diff > 0:
        tweet += " (+%0.3f" % (diff)
        tweet += "%)"
    elif diff < 0:
        tweet += " (%0.3f" % (diff)
        tweet += "%)"

    tweet += " #bitcoin"

    post_tweet(api, debug, tweet)

    redis.set('last_price', price_now)


if __name__ == "__main__":
    main(sys.argv[1:])
