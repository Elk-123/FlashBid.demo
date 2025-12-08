import redis
import os

# 配置 Redis 连接
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
r = redis.Redis(connection_pool=pool)

# ---------------------------------------------------------
# LUA 脚本：原子竞价
# ---------------------------------------------------------
LUA_BID_SCRIPT = """
local key = KEYS[1]
local new_price = tonumber(ARGV[1])
local user_id = ARGV[2]

-- 获取当前价格，如果不存在则默认为 0
local current_price = tonumber(redis.call('HGET', key, 'price')) or 0

if new_price > current_price then
    redis.call('HSET', key, 'price', new_price)
    redis.call('HSET', key, 'user_id', user_id)
    return 1
else
    return 0
end
"""

# 预加载脚本
bid_script_sha = r.script_load(LUA_BID_SCRIPT)

class RedisClient:
    @staticmethod
    def init_item(item_id: int, start_price: float):
        """初始化商品价格"""
        key = f"item:{item_id}"
        if not r.exists(key):
            r.hset(key, mapping={
                "price": start_price,
                "user_id": "system"
            })
            return True
        return False

    @staticmethod
    def get_current_info(item_id: int):
        """获取当前价格"""
        key = f"item:{item_id}"
        return r.hgetall(key)

    @staticmethod
    def place_bid(item_id: int, user_id: str, amount: float):
        """
        执行原子竞价
        """
        # --- 修正点：global 必须放在函数最开头 ---
        global bid_script_sha
        
        key = f"item:{item_id}"
        try:
            # 尝试执行脚本
            result = r.evalsha(bid_script_sha, 1, key, amount, user_id)
            return result == 1
        except redis.exceptions.NoScriptError:
            # 如果脚本丢失（例如 Redis 重启了），重新加载并执行
            print("⚠️ Redis Script missing, reloading...")
            bid_script_sha = r.script_load(LUA_BID_SCRIPT)
            result = r.evalsha(bid_script_sha, 1, key, amount, user_id)
            return result == 1

redis_client = RedisClient()