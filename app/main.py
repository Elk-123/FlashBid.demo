from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal, BidLog, Item, Base, engine
from app.redis_client import redis_client
import time
from fastapi.responses import HTMLResponse # <--- 新增这行
import os # <--- 新增这行

# 确保数据库表已创建
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlashBid Demo")

# --- Pydantic 模型 (用于请求体校验) ---
class InitRequest(BaseModel):
    item_id: int
    start_price: float

class BidRequest(BaseModel):
    item_id: int
    user_id: str
    amount: float

# --- 数据库依赖 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 异步任务：将竞价日志写入 PostgreSQL ---
def write_bid_log_to_pg(item_id: int, user_id: str, amount: float):
    db = SessionLocal()
    try:
        # 记录一条竞价流水
        bid_log = BidLog(item_id=item_id, user_id=user_id, bid_amount=amount)
        db.add(bid_log)
        
        # 同时更新商品表里的当前最高价 (为了数据归档)
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            item = Item(id=item_id, name=f"Item-{item_id}", current_price=amount)
            db.add(item)
        else:
            if amount > item.current_price:
                item.current_price = amount
        
        db.commit()
        print(f"📝 [PG-Async] Saved bid: {user_id} @ {amount}")
    except Exception as e:
        print(f"❌ [PG-Error] {e}")
    finally:
        db.close()

# --- API 接口 ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open(os.path.join("app", "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/init")
def init_auction(req: InitRequest, db: Session = Depends(get_db)):
    """
    初始化一场拍卖
    """
    # 1. 写入 PG (创建商品)
    item = db.query(Item).filter(Item.id == req.item_id).first()
    if not item:
        item = Item(id=req.item_id, name=f"Item-{req.item_id}", current_price=req.start_price)
        db.add(item)
    else:
        item.current_price = req.start_price
    db.commit()

    # 2. 写入 Redis (这是实际竞价用的)
    success = redis_client.init_item(req.item_id, req.start_price)
    
    return {"msg": "Auction Initialized", "redis_init": success, "start_price": req.start_price}

@app.get("/item/{item_id}")
def get_current_price(item_id: int):
    """
    获取当前价格 (直接读 Redis，速度快)
    """
    info = redis_client.get_current_info(item_id)
    if not info:
        raise HTTPException(status_code=404, detail="Item not found in Redis")
    return info

@app.post("/bid")
def place_bid(req: BidRequest, background_tasks: BackgroundTasks):
    """
    核心竞价接口
    """
    # 1. 直接在 Redis 执行原子竞价
    success = redis_client.place_bid(req.item_id, req.user_id, req.amount)

    if success:
        # 2. 只有 Redis 成功了，才把写数据库的任务扔到后台 (Write-Behind)
        # 这样用户不需要等待数据库写入完成就能收到响应
        background_tasks.add_task(write_bid_log_to_pg, req.item_id, req.user_id, req.amount)
        return {"status": "accepted", "new_price": req.amount}
    else:
        # 竞价失败 (价格低了或者手慢了)
        return {"status": "rejected", "msg": "Price too low or outdated"}