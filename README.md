<div align="center">

# 📘 FlashBid - High Concurrency Auction System

**English** | [简体中文](README_CN.md)

</div>

---

## 1. Project Overview

**FlashBid** is a real-time auction system designed to simulate high-concurrency scenarios (similar to eBay or flash sales).
This project aims to solve the **data inconsistency (overselling/overwriting)** and **high latency** issues caused by traditional database architectures when multiple users place bids simultaneously.

By introducing **Redis + Lua Atomic Locks** and a **Write-Behind (Asynchronous Write)** strategy, the system successfully ensures zero error in price calculation and achieves millisecond-level response times under high-pressure tests with 50+ concurrent bots.

---

## 2. Key Takeaways & Architecture

Through the development of this project, I have mastered the following architectural concepts and technical details:

### 🛠 Tech Stack
*   **Backend**: Python FastAPI (High-performance async framework)
*   **Cache**: Redis (Core logic carrier, handling hot data)
*   **Storage**: PostgreSQL (Data archiving and logging)
*   **Infrastructure**: Docker & Docker-Compose (Containerized deployment)
*   **Testing**: Python Threading (Simulating concurrent bots)

### 🏗 Architecture Design

The project adopts a **"Cache-First, Write-Behind"** architectural pattern:

1.  **Read/Write Separation (Logic Layer)**:
    *   **Hot Data**: Current highest price, bidder info. Handled entirely in Redis for speed.
    *   **Cold Data**: Bid history, item archives. Stored in PostgreSQL for auditing and persistence.

2.  **The Core Solution - Redis Lua Scripts**:
    *   **Problem**: In high concurrency, "Read Price" and "Update Price" are two separate actions. The time gap between them causes Race Conditions.
    *   **Solution**: Encapsulate logic using Lua scripts: `GET price -> COMPUTE -> SET price`.
    *   **Effect**: Lua scripts execute **Atomically** in Redis. This acts as an extremely efficient in-memory lock, preventing price conflicts at the root.

3.  **Asynchronous Processing**:
    *   Uses FastAPI's `BackgroundTasks` to move the time-consuming "Write to DB" operation out of the main thread.
    *   **Benefit**: Users receive a success response immediately after the Redis update (<5ms), without waiting for Database I/O.

### 🎨 Design Patterns
*   **Singleton**: Encapsulation of the Redis connection pool to reuse connections globally and prevent resource exhaustion.
*   **Dependency Injection**: `Depends(get_db)` in FastAPI to manage database session lifecycles gracefully.
*   **Optimistic Locking**: Updates occur only if the bid is higher than the current Redis value (similar to CAS - Compare-And-Swap).

---

## 3. Scalability & Optimization

Although this is an MVP (Minimum Viable Product), it can be upgraded for production environments in the following areas:

### 🚀 Performance & Architecture
1.  **Message Queue (MQ) for Peak Shaving**:
    *   *Current*: `BackgroundTasks` run in memory; logs are lost if the server crashes.
    *   *Optimization*: Introduce **RabbitMQ** or **Kafka**. After Redis success, send messages to the queue, and a separate Consumer service writes to the database.

2.  **Communication Protocol Upgrade (WebSocket)**:
    *   *Current*: Frontend uses `setInterval` polling, which causes latency and wastes bandwidth.
    *   *Optimization*: Use **WebSocket**. When Redis price updates, the server proactively Pushes messages to all online clients for real-time updates.

3.  **Distributed Lock**:
    *   *Current*: Lua scripts work perfectly on a single Redis instance.
    *   *Optimization*: If scaling to a Redis Cluster, introduce the Redlock algorithm to handle cross-node locking.

### 🛡 Security & Business Logic
1.  **Authentication**: Introduce **JWT (JSON Web Token)** to ensure only logged-in users can call the `/bid` endpoint.
2.  **Rate Limiting**: Limit bid frequency per User ID to prevent malicious scripts (using Redis `INCR` + `EXPIRE` for sliding windows).

---

## 4. Conclusion

FlashBid demonstrates that **"Direct Database Access" is not viable** for high-concurrency, high-consistency scenarios (like flash sales, ticket booking, auctions).

It is essential to introduce **Redis as a shield**, leverage its **Atomicity** for core logic, and use **Asynchronous** methods to decouple non-core logic. This is a crucial step towards becoming an advanced backend architect.

---

## 5. Quick Start

Follow these steps to run the project locally.

### 1. Setup & Dependencies
```bash
# 1. Activate Conda Environment
conda activate flashbid

# 2. Install Dependencies
pip install -r requirements.txt
```

### 2. Start Infrastructure
Start PostgreSQL and Redis using Docker Compose.
```bash
docker compose up -d
```

### 3. Check Environment Connectivity
```bash
python check_env.py
```

### 4. Verify Core Logic (No Web Server Needed)
Test the Redis atomic bidding logic directly without starting the web server.
```bash
python test_redis_logic.py
```

### 5. Start API Server
```bash
uvicorn app.main:app --reload
```
*   **API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. Safe Shutdown & Cleanup

After testing, it is recommended to follow these steps to stop services and release resources.

1.  **Stop Web Server**: Press `Ctrl + C` in the terminal.
2.  **Stop Infrastructure**:
    *   Pause (Keep Data): `docker compose stop`
    *   Remove Containers (Recommended): `docker compose down`
    *   Reset (Delete Data): `docker compose down -v`
3.  **Deactivate Environment**: `conda deactivate`