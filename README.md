这份文档完全按照你的要求进行了整合与定制。第一部分保留了你提供的经典的理论框架，将最终目标修正为本次的“FlashBid”项目；第二部分详细规划了 Python + Docker 的落地步骤，包含自动化竞拍脚本的设计。

你可以直接保存为 **`Guide.md`**，这将是你接下来开发的行动纲领。

***

# Guide.md: PostgreSQL & Redis 学习与实战路线图

## 🎯 学习目标
1.  **深度理解**：掌握 PostgreSQL（关系型）与 Redis（非关系型/缓存）的核心原理。
2.  **场景应用**：学会“什么数据存哪里”，理解 Cache-Aside、Write-Behind 等架构模式。
3.  **最终实战**：构建 **"FlashBid" (高并发实时竞拍系统)**，并编写自动化脚本模拟多人抢拍场景。

---

## 第一部分：核心理论基础

### 第一阶段：PostgreSQL —— 数据持久化的基石

#### 1. 是什么 (What)
PostgreSQL（简称 PG）是世界上最先进的开源**对象-关系型数据库 (ORDBMS)**。它不仅支持标准的 SQL，还极其强调扩展性和合规性。
*   **地位**：被誉为“开源界的 Oracle”，以稳定性、功能丰富著称。
*   **特点**：支持复杂查询、外键约束、事务（ACID）、以及强大的 JSONB 支持（让你像用 MongoDB 一样用 SQL）。

#### 2. 原理 (Principles)
*   **ACID 事务**：原子性、一致性、隔离性、持久性。确保银行转账这种操作要么全成功，要么全失败。
*   **MVCC (多版本并发控制)**：PG 的核心黑科技。读写互不阻塞，通过保存数据的多个历史版本来实现高并发下的数据一致性。
*   **WAL (预写式日志)**：先写日志，再写数据文件。保证断电后数据不丢失。
*   **Process Model**：PG 是多进程架构（不同于 MySQL 的多线程），每个连接通过一个独立的进程处理，极度稳定。

#### 3. 应用 (Applications)
*   **核心业务数据**：用户信息、订单、账单、库存（所有不能丢、关系复杂的数据）。
*   **地理信息系统 (GIS)**：配合 PostGIS 插件，是处理地图数据的王者。
*   **混合负载**：既有结构化数据，又有非结构化的 JSON 数据场景。

#### ✅ 练习重点
*   安装 PostgreSQL。
*   CRUD 操作，熟悉 `psql` 命令行。
*   理解索引（B-Tree, GIN）对性能的影响。
*   体验 JSONB 类型字段的查询。

---

### 第二阶段：Redis —— 极速的内存数据结构存储

#### 1. 是什么 (What)
Redis (Remote Dictionary Server) 是一个开源的**内存中**数据结构存储系统。它可以用作数据库、缓存和消息中间件。
*   **地位**：NoSQL 领域的性能之王，键值对（Key-Value）存储的代表。
*   **特点**：数据在内存中（纳秒级响应），单线程模型（避免上下文切换开销），支持丰富的数据结构。

#### 2. 原理 (Principles)
*   **In-Memory**：所有数据主要存储在 RAM 中，读写速度极快（10万+ QPS）。
*   **单线程事件循环 (Event Loop)**：核心处理逻辑是单线程的，利用 I/O 多路复用处理并发连接。**好处**：没有锁竞争，逻辑简单；**坏处**：不能执行耗时命令（会卡死所有请求）。
*   **持久化 (Persistence)**：
    *   **RDB**：定时快照（由子进程完成）。
    *   **AOF**：记录每条写命令（类似日志）。
*   **数据结构**：String, List, Set, Hash, ZSet (Sorted Set) 是其灵魂。

#### 3. 应用 (Applications)
*   **缓存 (Caching)**：减轻数据库压力（如热点新闻、商品详情）。
*   **会话管理 (Session)**：用户登录态保持。
*   **排行榜 (Leaderboard)**：利用 ZSet 实现实时排名。
*   **计数器/限流**：视频播放量、API 调用频率限制。
*   **分布式锁**：在多台服务器之间协调任务。

#### ✅ 练习重点
*   安装 Redis (或使用 Docker)。
*   熟练使用 `redis-cli`。
*   掌握 5 种基本数据结构的适用场景。
*   理解 TTL (过期时间) 的作用。

---

### 第三阶段：双剑合璧 —— 架构模式

在实际应用中，很少单独使用其中一个。我们需要学习它们如何协作：

1.  **Cache-Aside Pattern (旁路缓存模式)**：
    *   读：先查 Redis -> 没有则查 PG -> 写入 Redis -> 返回。
    *   写：更新 PG -> 删除 Redis 缓存。
2.  **Write-Behind (异步写入)**：
    *   高并发写入先存入 Redis，后台异步批量刷入 PG（适合点赞、浏览量、**以及本项目的竞拍记录**）。

---

## 第二部分：FlashBid 实战开发指引

### 第四阶段：项目实现步骤与技术细节

#### 1. 项目架构概览
我们将构建一个Web应用，用户可以在前端看到商品实时价格并出价。后台使用 Python 处理逻辑，模拟脚本将作为“机器人”参与竞价。

*   **语言**：Python 3.10+
*   **Web 框架**：FastAPI (因其高性能异步特性，完美匹配 Redis)
*   **数据库**：PostgreSQL 15 (数据落地), Redis 7 (热数据与消息分发)
*   **环境编排**：Docker Compose
*   **前端**：HTML + JavaScript (Fetch API + 简单的 DOM 操作)

#### 2. 目录结构规划
```text
flashbid/
├── docker-compose.yml       # 一键启动 PG 和 Redis
├── app/
│   ├── main.py              # FastAPI 后端核心代码
│   ├── database.py          # PG 连接与模型定义
│   ├── redis_client.py      # Redis 连接与 Lua 脚本
│   └── templates/
│       └── index.html       # 前端页面
├── scripts/
│   └── bot.py               # 模拟竞拍机器人脚本
└── requirements.txt         # Python 依赖
```

#### 3. 详细实施步骤

##### 步骤 A: 环境搭建 (Docker)
编写 `docker-compose.yml`，定义两个服务：
*   `db`: PostgreSQL 容器，设置好默认用户和密码，挂载数据卷持久化。
*   `redis`: Redis 容器，无需密码或设置简单密码。
*   *目标*：运行 `docker-compose up -d` 后，能通过工具连接到两个数据库。

##### 步骤 B: 数据库建模 (PostgreSQL)
在 `database.py` 中使用 SQLModel 或 SQLAlchemy 定义模型：
1.  **Item (拍品)**: `id`, `name`, `start_price`, `end_time`, `final_price`.
2.  **BidLog (出价记录)**: `id`, `item_id`, `user_name`, `bid_amount`, `bid_time`.
*   *关键点*：金额字段使用 `Decimal` 类型，严禁使用 Float。

##### 步骤 C: 核心竞价逻辑 (Redis + Python)
这是项目的灵魂。在 `redis_client.py` 中实现：
1.  **初始化**：从 PG 读取商品基础价格，写入 Redis String (Key: `auction:{id}:price`)。
2.  **原子出价 (关键)**：
    *   当用户请求出价时，**不能**简单地 `get` 然后 `set` (会有并发冲突)。
    *   **方案**：使用 Redis 的 `Lua 脚本` 或 `SETNX` 锁，或者利用 `INCRBY` (如果是固定加价) / `WATCH` 事务。
    *   逻辑：`IF new_bid > current_redis_bid THEN set new_bid AND return True ELSE return False`.
3.  **持久化策略**：
    *   使用 FastAPI 的 `BackgroundTasks`，在 Redis 更新成功后，异步将这条出价记录写入 PostgreSQL 的 `BidLog` 表。

##### 步骤 D: 前端页面与 API
1.  **API**:
    *   `GET /current_price/{item_id}`: 返回 Redis 中的价格。
    *   `POST /bid`: 接收 `{user_id, amount}`。
2.  **Web 页面**:
    *   展示当前价格（每秒轮询一次或使用 WebSocket）。
    *   一个巨大的“加价”按钮。
    *   实时显示“恭喜 User A 出价成功”或“出价太低被拒绝”。

##### 步骤 E: 编写“疯狂机器人”脚本 (模拟高并发)
在 `scripts/bot.py` 中实现：
*   使用 `threading` 或 `asyncio` + `aiohttp`。
*   **逻辑**：
    1.  启动 50 个线程 (模拟 50 个买家)。
    2.  每个线程在一个循环中，获取当前价格，并在当前价格基础上随机 +1 到 +10 元。
    3.  疯狂发送 POST 请求。
*   **观察**：观察控制台，看是否有“脏读”发生（即价格倒退），验证 Redis 锁机制是否有效。

##### 步骤 F: 部署与分享
为了让朋友能访问：
*   **方案一 (最简单)**：使用 `ngrok` 将本地 8000 端口映射到公网。
    *   命令：`ngrok http 8000` -> 发送生成的 URL 给朋友。
*   **方案二 (进阶)**：购买一台便宜的云服务器 (AWS/DigitalOcean)，安装 Docker，上传代码运行。

---

### 🚀 下一步行动
准备好开始了吗？
**第一步任务**：
1.  在本地新建文件夹 `flashbid`。
2.  确认已安装 Docker Desktop。
3.  告诉我，我将为你生成 `docker-compose.yml` 文件和基本的 Python 环境配置代码。
