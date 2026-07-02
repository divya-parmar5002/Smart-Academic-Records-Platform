from redis import Redis
from app.core.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
)

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    decode_responses=True,
)

def test_redis_connection():
    try:
        redis_client.ping()
        print("✅ Redis Connected Successfully")
    except Exception as e:
      print(f"❌ Redis Connection Error: {e}")