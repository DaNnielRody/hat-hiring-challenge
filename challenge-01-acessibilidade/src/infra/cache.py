from cachetools import TTLCache

cache: TTLCache = TTLCache(maxsize=100, ttl=60)
