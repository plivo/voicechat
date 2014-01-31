import os
import time
import base64
import redis
import config
import plivo

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"): 
    return ((num == 0) and  "0" ) or (baseN(num // b, b).lstrip("0") + numerals[num % b])

def tinyid(size=6):
    id = '%s%s' % (
            baseN(abs(hash(time.time())), 36), 
            baseN(abs(hash(time.time())), 36))
    return id[0:size]

def get_redis_connection():
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
    rd = redis.from_url(redis_url)
    return rd

def get_plivo_connection():
    pl = plivo.RestAPI(config.PLIVO_AUTH_ID, config.PLIVO_AUTH_TOKEN)
    return pl
