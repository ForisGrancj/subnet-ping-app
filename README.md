# 🌐 Subnet Ping & Query Logger Service
> *An asynchronous microservice for scanning CIDR subnets, monitoring host availability via ICMP, and caching real-time network states using Django, Celery, Redis, and PostgreSQL.*

---

## 📖 About

When managing modern network infrastructure, scanning large IP ranges synchronously can lead to high latency, server
timeouts, and poor user experience.

**Subnet Ping & Query Logger Service** solves this problem by offloading heavy ICMP network scanning tasks to 
asynchronous background workers. It validates CIDR-formatted IP inputs, queues scanning tasks via
**Celery & Redis**, performs non-blocking ping checks, bulk-saves the results into a **PostgreSQL** database,
and caches responses for high-speed retrieval.

---

## ✨ Features

* **Asynchronous Task Processing:** Non-blocking API execution using Celery workers and Redis message broker.
* **Smart Caching Layer:** Caches query results in Redis for 1 hour (3600s) to minimize unnecessary database reads and network scans.
* **Efficient Bulk Writes:** Writes all host ping statuses into PostgreSQL using `bulk_create` to optimize DB I/O performance.
* **ICMP Network Monitoring:** Powered by `icmplib` and `ipaddress` for reliable, low-overhead IP availability checks.
* **Dockerized Architecture:** Entire stack (Django, Celery, Redis, PostgreSQL) is containerized with custom healthcheck dependency management.
* **Production-Ready Admin Interface:** Fully registered models in Django Admin for visual network log tracking.

---

## 📁 Project Directory Structure

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
    ├── serializers.py          # DRF serializers & IP validations
    ├── tasks.py                # Celery async tasks (ICMP Ping logic)
    ├── views.py                # API views & endpoints
    ├── urls.py                 # App-specific URL routes
    └── models/                 # Database models
        ├── __init__.py
        ├── SubnetQueryLog.py   # Parent query history model
        └── PingResultLog.py    # Individual IP ping status model
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
               |   - Subnet Validation (serializers.py)          |
               |   - Primary Log Record Creation (views.py)      |
               |   - Dispatch Async Task (.delay)                |
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
     | - Result Backend / Cache     |   | - PingResultLog              |
     +--------------+---------------+   +------------------------------+
                   |                                ^
         Consume Task (Workers)                     |
                  |                          Bulk Write
                  v                                 |
     +------------------------------------------------+------------+
     |                  CELERY WORKER (celery_worker)              |
     |                                                             |
     |           - Asynchronous IP Scanning (icmplib)              |                                  
     |           - Result Caching (cache.set - 3600s)              |
     |           - Bulk Database Insertion (bulk_create)           |
     |                                                             |
     +-------------------------------------------------------------+
```

## System Topology & Flow Algorithm

### Execution Sequence Diagram
``` mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as Django API (Views/Serializers)
    participant DB as PostgreSQL DB
    participant Queue as Redis Queue
    participant Worker as Celery Worker
    participant Cache as Redis Cache

    Note over Client, API: Step 1 & 2: Validation & Database Logging
    Client->>API: POST /api/ping/ {"subnet": "192.168.1.0/28"}
    API->>API: SubnetPingSerializer validates CIDR
    API->>DB: SubnetQueryLog.objects.create()
    DB-->>API: Returns query_id

    Note over API, Client: Step 3 & 4: Queueing & Immediate Response
    API->>Queue: process_subnet_ping_task.delay(query_id, subnet)
    API-->>Client: 202 ACCEPTED {"query_id": query_id}

    Note over Queue, Worker: Step 5: Background Processing
    Queue->>Worker: Consume ping task
    Worker->>Worker: Extract IPs & run ICMP ping (icmplib)

    Note over Worker, Cache: Step 6: Bulk Write & Caching
    Worker->>DB: PingResultLog.objects.bulk_create()
    Worker->>Cache: cache.set("subnet_logs_{query_id}", TTL: 3600s)
```

### Execution Steps
1. **Request & Validation:** Client posts a CIDR network block (e.g. `192.168.1.0/28`). `SubnetPingSerializer` verifies validity.
2. **Database Logging:** System creates a parent `SubnetQueryLog` record in PostgreSQL and generates a tracking `query_id`.
3. **Queueing:** Task `process_subnet_ping_task.delay(query_log.id, subnet_str)` is pushed to Redis.
4. **Immediate Response:** API instantly returns `202 ACCEPTED` status with the `query_id` to prevent client blocking.
5. **Background Scan:** Celery worker extracts host IP addresses and runs ICMP ping checks (`icmplib.ping`).
6. **Bulk Insert & Caching:** Worker bulk-saves host statuses to PostgreSQL (`PingResultLog`) and updates the Redis cache key `subnet_logs_{query_id}` (TTL: 1 hour).