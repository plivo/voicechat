import base64
import config
from contextlib import contextmanager
import os
import plivo
import random
import redis
import urlparse


# Set up the redis pool, with some url parsing logic
# See redis.client.StrictRedis.from_url for a reference
#    (It would have been nice if py-redis exported from_url)
def _make_redis_pool():
    url = urlparse(config.REDIS_URL)
    assert url.scheme == 'redis' or not url.scheme
    try:
        db = int(url.path.replace('/', ''))
    except:
        db = 0
    return redis.BlockingConnectionPool(
        max_connections = config.REDIS_MAX_CONNECTIONS,
        timeout = config.REDIS_TIMEOUT,
        host = url.hostname,
        port = int(url.port or 6379),
        db = db,
        password = url.password,
    )
_pool = _make_redis_pool()

            
def make_id(size=6):
    """Generate a base-36 encoded string of the specified size.
    
    The string is gaurunteed to be unique since the last time redis was
    rebooted. This uses redis' INCR command for an atomic
    get-and-increment on an ID key, to avoid race conditions. As such,
    this function is fully thread and process safe. Avoid using this if
    you don't need that gauruntee.
    """
    # NB: Do we want to use capital letters? More traditional for Base36
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    with redis_client() as redis:
        unique_val = redis.incr('ID_AUTO_INCR', 1)
    rand = random.Random(unique_val)
    return ''.join(random.choice(alphabet) for _ in range(size))


@contextmanager
def redis_client():
    """Context manager that provides a redis client connection.
    
    This is thread-safe and process-safe. It may potentially block
    for up to config.REDIS_TIMEOUT seconds, though (at which
    point it will fail with an exception).
    """
    client = redis.StrictRedis(connection_pool=_pool)
    yield client
    _pool.release(client)
    

def get_plivo_connection():
    return plivo.RestAPI(config.PLIVO_AUTH_ID, config.PLIVO_AUTH_TOKEN)
