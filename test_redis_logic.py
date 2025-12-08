# test_redis_logic.py
from app.redis_client import redis_client, r

def test_workflow():
    item_id = 999
    user_a = "Alice"
    user_b = "Bob"
    
    print(f"--- 开始测试 Redis 逻辑 (Item ID: {item_id}) ---")
    
    # 1. 清理环境 (确保从头开始)
    r.delete(f"item:{item_id}")
    
    # 2. 初始化商品，起拍价 100
    redis_client.init_item(item_id, 100.0)
    info = redis_client.get_current_info(item_id)
    print(f"✅ 初始化完成: {info}")
    
    # 3. Alice 出价 105 (应该成功)
    success = redis_client.place_bid(item_id, user_a, 105.0)
    print(f"👤 Alice 出价 105: {'✅ 成功' if success else '❌ 失败'}")
    
    # 4. Bob 出价 102 (应该失败，因为比 105 低)
    success = redis_client.place_bid(item_id, user_b, 102.0)
    print(f"👤 Bob 出价 102: {'✅ 成功' if success else '❌ 失败 (预期内)'}")
    
    # 5. Bob 不服，出价 110 (应该成功)
    success = redis_client.place_bid(item_id, user_b, 110.0)
    print(f"👤 Bob 出价 110: {'✅ 成功' if success else '❌ 失败'}")
    
    # 6. 最终确认
    final_info = redis_client.get_current_info(item_id)
    print(f"🏁 最终状态: {final_info}")
    
    # 简单的断言
    assert float(final_info['price']) == 110.0
    assert final_info['user_id'] == user_b
    print("\n✨ 所有 Redis 逻辑测试通过！")

if __name__ == "__main__":
    test_workflow()