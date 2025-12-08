import redis
from sqlalchemy import create_engine, text
import time

# --- 配置信息 ---
# 注意：因为我们在本机运行脚本，所以 host 是 'localhost'
PG_URL = "postgresql://admin:password123@localhost:5433/flashbid_db"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

def check_redis():
    print("Testing Redis connection...", end=" ")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.set("test_key", "Hello FlashBid!")
        val = r.get("test_key")
        if val == "Hello FlashBid!":
            print("✅ Success! (Read/Write OK)")
        else:
            print("❌ Failed (Value mismatch)")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_postgres():
    print("Testing PostgreSQL connection...", end=" ")
    try:
        engine = create_engine(PG_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Success! (Query OK)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("--- FlashBid Environment Check ---")
    check_redis()
    check_postgres()
    print("----------------------------------")