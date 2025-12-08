from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ---------------------------------------------------------
# ✅ 数据库连接配置
# ---------------------------------------------------------
# 注意：这里的用户名密码 (admin/password123) 必须和你 docker-compose.yml 里配置的一致
SQLALCHEMY_DATABASE_URL = "postgresql://admin:password123@localhost:5433/flashbid_db"

# 创建引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# --- 定义数据模型 (Models) ---

class Item(Base):
    """商品表"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # ✅ 修改点 1: 为了匹配 main.py，将 start_price 改为 current_price
    # 同时保留 Numeric 类型，适合金额存储
    current_price = Column(Numeric(10, 2), default=0.00)
    
    # 记录最后更新时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BidLog(Base):
    """出价记录表"""
    __tablename__ = "bid_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联商品
    item_id = Column(Integer, ForeignKey("items.id"), index=True)
    
    # ✅ 修改点 2: 为了匹配 main.py，将 user_name 改为 user_id
    user_id = Column(String, index=True)
    
    # 出价金额
    bid_amount = Column(Numeric(10, 2))
    
    # 出价时间
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- 工具函数 ---

def init_db():
    """建表工具"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database Tables Created Successfully!")

def get_db():
    """FastAPI 依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()