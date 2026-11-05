# Subnet Ping & Query Logger Service
> *An asynchronous microservice for scanning CIDR subnets, 
> monitoring host availability via ICMP, and caching real-time 
> network states using Django, Celery, Redis, and PostgreSQL.*

---

## About

When managing modern network infrastructure, scanning large IP ranges synchronously can lead to high latency, server
timeouts, and poor user experience.

**Subnet Ping & Query Logger Service** solves this problem by offloading heavy ICMP network scanning tasks to 
asynchronous background workers. It validates CIDR-formatted IP inputs, queues scanning tasks via
**Celery & Redis**, performs non-blocking ping checks, bulk-saves the results into a **PostgreSQL** database,
and caches responses for high-speed retrieval.

---

## Configuration

Secrets are read from environment variables, not stored in the repository.

```bash
cp .env.example .env   # then set DJANGO_SECRET_KEY and DB_PASSWORD
docker compose up --build
```

---

## Features

* **Multi-Tiered Query Resolution:** Redis-First $\rightarrow$ Database Fallback $\rightarrow$ Celery Worker Execution flow for minimum latency.
* **Smart Caching Layer:** Caches query results in Redis for 1 hour (3600s) to eliminate redundant network scans.
* **Optimized Log API:** Employs `prefetch_related` on `query_id` lookups to eliminate N+1 SQL queries.
* **Asynchronous Task Processing:** Non-blocking API execution using Celery workers and Redis message broker.
* **Efficient Bulk Writes:** Bulk-inserts ping outcomes into PostgreSQL (`PingResultLog`) via `bulk_create`.
* **ICMP Network Monitoring:** Powered by `icmplib` and `ipaddress` for reliable, low-overhead IP availability checks.
* **Dockerized Architecture:** Entire stack (Django, Celery, Redis, PostgreSQL) is containerized with healthcheck-based dependency management.

---
## API Endpoints & Usage

| Method | Endpoint | Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/ping/` | Triggers a new subnet ICMP scan or returns cached/historical results. | `subnet_value`, `subnet`, or `subnet_input` (JSON body) |
| **`GET`** | `/logs/` | Lists query history or fetches a specific log by `query_id` or `subnet`. | `query_id` or `subnet` / `subnet_value` (URL query parameters) |

### 1. Execute Subnet Scan (`POST /ping/`)

Creates a new background scan task or fetches results from **Redis Cache** / **PostgreSQL Fallback**.

**Request Payload:**
``` json
{
  "subnet_value": "127.0.0.0/30"
}
```
**cURL Command:**
``` bash
curl -X POST http://localhost:8000/ping/ \
  -H "Content-Type: application/json" \
  -d '{"subnet_value": "127.0.0.0/30"}'
## Project Directory Structure
``` 
**New Scan Task Created (HTTP 201 Created)**
``` json
{
  "message": "Subnet ping task created successfully.",
  "id": 43
}
```
**Redis Cache Hit (HTTP 200 OK)**
``` json
{
  "message": "the subnet value is already exist with 42",
  "source": "Redis Cache",
  "data": [
    {
      "ip_address": "127.0.0.1",
      "is_active": true,
      "rtt": 0.45
    }
  ]
}
```
### 2.Query Logs & Specific Scan Details (GET /logs/)
Retrieves historical query logs or fetches details for a specific **query_id** using optimized **prefetch_related** queries.

**Fetch by query_id**
``` bash
curl -X GET "http://localhost:8000/logs/?query_id=42"
```
**Response (HTTP 200 OK):**
``` json
{
  "source": "Database",
  "data": {
    "id": 42,
    "subnet_input": "127.0.0.0/30",
    "status": "COMPLETED",
    "created_at": "2026-08-05T10:15:52Z",
    "results": [
      {
        "ip_address": "127.0.0.1",
        "is_active": true/false,
        "rtt": 0.45/null
      }
    ]
  }
}
```
**Fetch by subnet:**
``` bash
curl -X GET "http://localhost:8000/logs/?subnet=127.0.0.0/30"
```
**Fetch All Logs History:**
``` bash
curl -X GET "http://localhost:8000/logs/"
```

## Project Directory Structure

 mermaid
DjangoProject1/
├── manage.py                   
├── Dockerfile                  
├── docker-compose.yml          
├── requirements.txt            # Python dependencies
├── db_dump.sql                 # PostgreSQL database dump file
├── subnet_ping_prj/            # Project core configuration directory
│   ├── __init__.py
│   ├── settings.py             # Global settings (DB, Cache, Apps)
│   ├── urls.py                 
│   ├── celery.py               # Celery instance setup
│   └── wsgi.py                 
└── subnet_app/                 # Main application directory
    ├── admin.py                # Django Admin panel configuration
    ├── apps.py                 # Application configuration
    ├── serializers/            # DRF serializers & IP validations
    ├── tasks.py                # Celery async tasks (ICMP Ping logic)
    ├── views/                  # API views & endpoints (PingCreate, LogList)
    ├── urls.py                 # App-specific URL routes
    └── models/                 # Database models
        ├── __init__.py
        ├── SubnetQueryLog.py   # Parent query history model (subnet_input, status)
        └── PingResultLog.py    # Individual IP ping status model

## System Topology & Flow Algorithm

``` 
              +-------------------------------------------------+
               |                   CLIENT                        |
               |       (Postman / Web Browser / API App)         |
               +-----------------------+-------------------------+
                                       |
                                HTTP GET / POST
                                       |
                                       v
               +-------------------------------------------------+
               |             Port 8000 (Docker)                  |
               |                                                 |
               |            DJANGO REST FRAMEWORK (web)          |
               |   1. Check Redis Cache  (cache.get)             |
               |   2. Check PostgreSQL   (subnet_input fallback) |
               |   3. Create Record & Dispatch Celery Task       |
               +-------------------+-----------------------------+
                                   |
                  +----------------+----------------+
                  |                                 |
         Dispatch Task / Get Cache              SQL Queries
                  |                                 |
                  v                                 v
     +------------------------------+   +------------------------------+
     |   REDIS (redis:6379)         |   | POSTGRESQL (db:5432)         |
     |                              |   |                              |
     | - Message Broker (Queue)     |   | - SubnetQueryLog             |
     | - Result Cache (3600s TTL)   |   | - PingResultLog              |
     +--------------+---------------+   +------------------------------+
                   |                                ^
         Consume Task (Workers)                     |
                  |                          Bulk Write
                  v                                 |
     +-------------------------------------------------------------+
     |                  CELERY WORKER (celery_worker)              |
     |                                                             |
     |           - Asynchronous IP Scanning (icmplib)              |                                  
     |           - Result Caching (cache.set - 3600s)              |
     |           - Bulk Database Insertion (bulk_create)           |
     |                                                             |
     +-------------------------------------------------------------+
```

### Execution Sequence Diagram
``` mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as Django API (Views)
    participant Cache as Redis Cache
    participant DB as PostgreSQL DB
    participant Queue as Redis Queue
    participant Worker as Celery Worker

    Client->>API: POST /ping/ {"subnet_value": "192.168.1.0/28"}
    
    Note over API, Cache: Step 1: Redis Cache Lookup
    API->>Cache: cache.get("subnet_scan:192.168.1.0/28")
    alt Cache Hit
        Cache-->>API: Returns cached JSON results
        API-->>Client: 200 OK {"source": "Redis Cache", "data": [...]}
    end

    Note over API, DB: Step 2: PostgreSQL Database Fallback
    API->>DB: SubnetQueryLog.objects.filter(subnet_input=...)
    alt DB Match Found
        DB-->>API: Returns existing SubnetQueryLog (e.g. ID: 42)
        API->>Cache: Repopulate Redis Cache (TTL: 3600s)
        API-->>Client: 200 OK {"message": "the subnet value is already exist with 42", "source": "Database Fallback"}
    end

    Note over API, Worker: Step 3: Brand New Subnet Scan
    API->>DB: SubnetQueryLog.objects.create(subnet_input=...)
    DB-->>API: Returns new record (ID: 43)
    API->>Queue: process_subnet_ping.delay(43, "192.168.1.0/28")
    API-->>Client: 201 CREATED {"id": 43, "message": "Subnet ping task created successfully."}
    
    Queue->>Worker: Consume async task
    Worker->>Worker: ICMP Ping Range (icmplib)
    Worker->>DB: PingResultLog.objects.bulk_create()
    Worker->>Cache: cache.set("subnet_scan:192.168.1.0/28", results, 3600)
```

### Execution Steps
1. **Request Input:** Client sends payload {"subnet_value": "192.168.1.0/28"} to /ping/.
2. **Redis Cache Check:** The API checks key subnet_scan:<subnet_input>. If found, returns 200 OK with cached hosts instantly.
3. **Database Fallback:** If cache misses/expires, it queries SubnetQueryLog by subnet_input. If found, re-caches results into Redis and returns existing query ID 200 OK.
4. **New Task Creation:** If record exists nowhere, creates SubnetQueryLog(subnet_input=...), returns 201 CREATED, and dispatches Celery task.
5. **Background Scan & Bulk Write:** Celery executes ICMP checks via icmplib, performs bulk_create on PingResultLog, updates log status, and primes Redis cache with a 1-hour TTL.
6. **Optimized Log Querying:** GET /logs/?query_id=1 fetches query history and pre-fetches nested ping results using prefetch_related('results') for optimal SQL performance.