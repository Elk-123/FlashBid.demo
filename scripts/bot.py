import requests
import threading
import time
import random

# 配置
BASE_URL = "http://127.0.0.1:8000"
ITEM_ID = 1
TOTAL_BOTS = 50  # 50个机器人

def get_current_price():
    """获取当前市场的真实价格"""
    try:
        resp = requests.get(f"{BASE_URL}/item/{ITEM_ID}")
        data = resp.json()
        # 如果 Redis 里没数据（比如刚重启），默认当做 0
        return float(data.get('price', 0))
    except Exception as e:
        print(f"⚠️ 获取价格失败: {e}")
        return 0.0

def bot_task(bot_id, base_price):
    """
    机器人策略：
    在【当前起步价】的基础上，随机加 1 ~ 100 元
    这样保证大家出的价大部分都比现在的有效
    """
    user_id = f"SmartBot-{bot_id}"
    
    # 模拟反应时间 (0.01 ~ 0.2秒)
    time.sleep(random.uniform(0.01, 0.2))
    
    # 决定出价：基准价 + 随机增量
    # 注意：这里模拟的是大家几乎同时看到基准价，然后各自做决定的场景
    increment = random.randint(1, 100) 
    my_price = base_price + increment

    try:
        # 发送出价请求
        response = requests.post(f"{BASE_URL}/bid", json={
            "item_id": ITEM_ID,
            "user_id": user_id,
            "amount": my_price
        })
        result = response.json()
        
        # 打印简略日志
        if result.get("status") == "accepted":
            print(f"✅ [成功] {user_id} 出价 {my_price}")
        else:
            # 失败很正常，说明别人手更快，出价比你更高
            # print(f"❌ [失败] {user_id} 出价 {my_price}") 
            pass # 为了版面整洁，失败的就不刷屏了，或者你可以取消注释
            
    except Exception as e:
        print(f"⚠️ [错误] {user_id}: {e}")

def run_simulation():
    # 1. 既然是“人机大战”，我们就不重置拍卖了，直接接着现在的价格玩
    # reset_auction() <--- 注释掉这行
    
    # 2. 获取当前起步价
    current_price = get_current_price()
    print(f"--- 🤖 智能机器人启动 ---")
    print(f"👀 监测到当前价格: {current_price}")
    print(f"🚀 50 个机器人正在计算加价策略...\n")
    
    threads = []
    # 3. 创建线程
    for i in range(TOTAL_BOTS):
        # 把当前价格传给机器人，作为参考
        t = threading.Thread(target=bot_task, args=(i, current_price))
        threads.append(t)
        
    # 4. 并发启动
    start_time = time.time()
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    # 5. 验证结果
    time.sleep(0.5) # 等一小会儿让子弹飞
    final_price = get_current_price()
    print(f"\n🏁 这一轮结束！")
    print(f"📈 价格从 {current_price} 飙升到了 -> {final_price}")

if __name__ == "__main__":
    run_simulation()