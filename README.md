# DIVA

## Distributed Intelligence for Vehicle Autonomy

DIVA is a prototype Vehicle-to-Vehicle (V2V) system in which each vehicle runs a local vision-language model on its own camera feed and broadcasts **compact semantic messages** — not raw video — to nearby vehicles.

Instead of transmitting a 10 MB video stream, a vehicle transmits roughly 300 bytes:

```json
{
  "vehicle_id": "Vehicle_A_Node",
  "event_type": "emergency",
  "object_type": "overturned_truck",
  "confidence": 0.92,
  "risk_level": "CRITICAL",
  "position": { "latitude": 37.7750, "longitude": -122.4190 },
  "description": "An overturned truck is blocking the right lane.",
  "recommendation": "change_lane_if_safe",
  "timestamp": "2026-08-22T10:14:03.221Z"
}
```

A receiving vehicle can act on this before the hazard enters its own sensor range.

> **Scope note.** This is a working prototype built for a hackathon, not a production or road-safe system. The [Known Limitations](#known-limitations) section is deliberately detailed — please read it before evaluating the project.

---

## Table of Contents

- [What Is Implemented](#what-is-implemented)
- [Architecture](#architecture)
- [The Semantic Message Contract](#the-semantic-message-contract)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Setup](#setup)
- [Running the Demo](#running-the-demo)
- [Backend API](#backend-api)
- [Database](#database)
- [Configuration Reference](#configuration-reference)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Team](#team)
- [License](#license)

---

## What Is Implemented

Everything in this table exists in the repository and runs today.

| Component | Status | File |
|---|---|---|
| Local VLM perception (Ollama / moondream) | ✅ Working | `edge_connections/ai_models.py` |
| Schema-constrained JSON output from the VLM | ✅ Working | `ai_models.py` (`format=` argument) |
| Vehicle A publisher loop (video → AI → MQTT) | ✅ Working | `edge_connections/vehicle_a_main.py` |
| H3 geospatial topic addressing | ✅ Working | `vehicle_a_main.py` |
| Vehicle B subscriber + alert display | ✅ Working | `edge_connections/vehicle_b_reciever.py` |
| MQTT transport over public broker | ✅ Working | both vehicle scripts |
| Shared Pydantic contract across all layers | ✅ Working | `backend/app/schemas/semantic_message.py` |
| FastAPI backend + event persistence | ✅ Working | `backend/app/main.py` |
| PostgreSQL storage via SQLAlchemy 2.0 | ✅ Working | `backend/app/models/` |
| Alembic migrations | ✅ Working | `backend/alembic/` |
| Event inspection CLI | ✅ Working | `backend/view_events.py` |
| WebSocket connection manager | ⚠️ Built, **not used by the vehicle clients** | `backend/app/websocket/` |
| YOLOv8 detector class | ⚠️ Written, **not yet wired into the pipeline** | `edge_connections/yolo_logic.py` |

Anything not in this table — Redis, RabbitMQ, Docker, MQTT-over-TLS, multi-vehicle fleets — is on the [Roadmap](#roadmap) and is **not** implemented.

---

## Architecture

The implemented data flow is MQTT-based:

```
                    ┌──────────────── VEHICLE A (Laptop A) ────────────────┐
                    │                                                      │
   test.mp4  ──────►│  OpenCV frame capture                                │
                    │        ↓  (every 2 seconds)                          │
                    │  Ollama VLM (moondream)                              │
                    │        ↓                                             │
                    │  SemanticMessage (schema-validated JSON)             │
                    │        ↓  (only if event_type != "normal")           │
                    │  MQTT publish → intelligence/{h3_cell}/hazard        │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                              broker.hivemq.com:8000 (WebSocket)
                                            │
                    ┌───────────────────────▼──────────────────────────────┐
                    │  MQTT subscribe → intelligence/+/hazard              │
                    │        ↓                                             │
                    │  Pydantic re-validation                              │
                    │        ↓                                             │
                    │  Alert printed to Vehicle B dashboard                │
                    │        ↓                                             │
                    │  HTTP POST → FastAPI /events                         │
                    └───────────────────────┬──────────────────────────────┘
                    └──────────── VEHICLE B (Laptop B) ────────────────────┘
                                            │
                    ┌───────────────────────▼──────────────────────────────┐
                    │  FastAPI backend → SQLAlchemy → PostgreSQL           │
                    └──────────────────────────────────────────────────────┘
```

### Design principles

**Semantic over raw.** Perception happens at the edge. Only the meaning is transmitted. Bandwidth drops by roughly four orders of magnitude versus video streaming.

**One schema, four layers.** `SemanticMessage` is a single Pydantic model used as the LLM output grammar, the MQTT wire format, the API request body, and the ORM mapping source. A malformed message cannot enter the system at any layer.

**Geospatial addressing.** Vehicle A converts its GPS position to an [H3](https://h3geo.org/) cell (resolution 9, ~174 m edge) and publishes to a topic derived from that cell. MQTT topic matching then acts as a coarse geographic filter. See [Known Limitations](#known-limitations) — the current subscriber does not yet exploit this.

---

## The Semantic Message Contract

Defined in `backend/app/schemas/semantic_message.py`.

| Field | Type | Constraint |
|---|---|---|
| `vehicle_id` | `str` | — |
| `event_type` | `Literal` | `hazard` \| `obstacle` \| `traffic` \| `emergency` \| `normal` |
| `object_type` | `str` | — |
| `confidence` | `float` | `0.0 ≤ x ≤ 1.0` |
| `risk_level` | `Literal` | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `position` | `Position` | `{ latitude: float, longitude: float }` |
| `description` | `str` | one sentence, enforced by prompt |
| `recommendation` | `str` | e.g. `slow_down`, `change_lane_if_safe` |
| `timestamp` | `datetime` | ISO 8601 |

This model is passed directly to Ollama as `format=SemanticMessage.model_json_schema()`, which constrains the model's decoding so it cannot emit a structurally invalid message.

---

## Repository Layout

```
.
├── alembic.ini
├── requirements.txt
├── .env.example
├── README.md
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── d29adea8a8ce_init.py     # creates events + vehicles tables
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py                # pydantic-settings, reads .env
│   │   ├── db/
│   │   │   ├── database.py              # engine + declarative Base
│   │   │   └── session.py               # SessionLocal + get_db dependency
│   │   ├── models/
│   │   │   ├── event.py                 # Event ORM model
│   │   │   └── vehicle.py               # Vehicle ORM model (not yet used)
│   │   ├── schemas/
│   │   │   └── semantic_message.py      # the shared contract
│   │   ├── websocket/
│   │   │   ├── manager.py               # ConnectionManager
│   │   │   └── handlers.py              # /ws/{vehicle_id} route
│   │   └── main.py                      # FastAPI app
│   │
│   ├── test_db.py                       # DB connectivity check
│   └── view_events.py                   # print stored events
│
└── edge_connections/
    ├── ai_models.py                     # Ollama VLM wrappers + prompt
    ├── vehicle_a_main.py                # publisher node
    ├── vehicle_b_reciever.py            # subscriber node
    ├── yolo_logic.py                    # YOLOv8 detector (not yet wired in)
    └── test.mp4                         # sample dashcam footage
```

---

## Requirements

- **Python 3.10+** (the codebase uses `str | None` union syntax)
- **[Ollama](https://ollama.com/)** installed and running locally, with the `moondream` model pulled
- **PostgreSQL** — a hosted Supabase instance or a local server
- A machine that can run a small VLM. CPU-only works but inference takes 2–5 s per frame.

`requirements.txt`:

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg2-binary
python-dotenv
opencv-python
paho-mqtt
h3
ollama
requests
ultralytics
```

---

## Setup

**1. Clone and enter the project**

```bash
git clone https://github.com/AaritShrama/V2V_COMMUNICATION_FOR_DISTRIBUTED_AI_SYSTEMS.git
cd V2V_COMMUNICATION_FOR_DISTRIBUTED_AI_SYSTEMS
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Copy `.env.example` to `.env` in the project root and fill in your own database URL:

```env
DATABASE_URL=postgresql://username:password@host:5432/database
```

> `DATABASE_URL` has **no default value** in `config.py`. The application will refuse to start if `.env` is missing. This is intentional — credentials must never be committed to the repository.

**5. Set up the AI model**

```bash
ollama pull moondream
ollama serve        # if not already running as a service
```

**6. Apply database migrations**

```bash
alembic upgrade head
```

**7. Verify the database connection**

```bash
python -m backend.test_db
# expected: Database connection successful: 1
```

---

## Running the Demo

The demo uses two machines (or two terminals on one machine) representing Vehicle A and Vehicle B.

### Terminal 1 — Backend

Run from the project root:

```bash
python -m uvicorn backend.app.main:app --reload
```

Available at `http://127.0.0.1:8000`, interactive docs at `http://127.0.0.1:8000/docs`.

### Terminal 2 — Vehicle B (receiver)

Start the receiver **before** the publisher so it does not miss the first broadcast.

```bash
cd edge_connections
python vehicle_b_reciever.py
```

Vehicle B connects to the broker, subscribes to `intelligence/+/hazard`, and forwards every validated alert to the backend.

### Terminal 3 — Vehicle A (publisher)

```bash
cd edge_connections
python vehicle_a_main.py
```

Vehicle A plays `test.mp4` in an OpenCV window, sends a frame to the VLM every 2 seconds, and publishes any non-`normal` result to its H3 topic. Press **`q`** in the video window to quit.

> **Note:** the video window freezes during inference. The VLM call is synchronous and blocks the render loop for 2–5 seconds per scan. This is a known issue — see [Known Limitations](#known-limitations).

### Expected output

**Vehicle A:**
```
[System] Starting Time-Based Edge AI Pipeline...

[10:14:03] ⏱️ 2 Seconds passed! Scanning frame...
   -> Result: EMERGENCY | Risk: CRITICAL
   -> Detail: A person is lying in the roadway ahead.
   -> [MQTT] Broadcasting threat to Hex: 8928308280fffff
```

**Vehicle B:**
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
🚨 [WARNING] V2V ALERT RECEIVED 🚨
   From Node : Vehicle_A_Node
   Event     : EMERGENCY
   Risk Level: CRITICAL
   Detail    : A person is lying in the roadway ahead.
   Action    : stop_if_necessary
   Cloud Sync: Status 200
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

### Inspecting stored events

```bash
python -m backend.view_events
```

---

## Backend API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check. Returns `{"status": "healthy", "service": "av-backend"}`. |
| `POST` | `/events` | Accepts a `SemanticMessage`, persists it, returns the assigned `event_id`. |
| `WS` | `/ws/{vehicle_id}` | Persistent vehicle connection. Messages received are broadcast to all connected clients. |

**`POST /events`** performs full Pydantic validation before writing. An out-of-range `confidence` or an unrecognised `risk_level` is rejected with `422`.

**`/ws/{vehicle_id}`** is implemented and functional, but the current vehicle clients communicate over MQTT and do not connect to it. It exists as the foundation for the planned broker-mediated routing described in the [Roadmap](#roadmap).

---

## Database

Two tables, created by migration `d29adea8a8ce_init`.

**`events`** — one row per received semantic message.

| Column | Type |
|---|---|
| `id` | `Integer`, PK, autoincrement |
| `vehicle_id` | `String(50)` |
| `event_type` | `String(30)` |
| `object_type` | `String(100)` |
| `confidence` | `Float` |
| `risk_level` | `String(20)` |
| `latitude`, `longitude` | `Float` |
| `description` | `String(500)` |
| `recommendation` | `String(500)` |
| `timestamp` | `DateTime` |

**`vehicles`** — schema for fleet registration (`vehicle_id`, `status`, `last_seen`). The table is created but **not yet written to**; vehicle registration is on the roadmap.

### Migration commands

```bash
alembic revision --autogenerate -m "description"   # after changing models
alembic upgrade head                                # apply
alembic downgrade -1                                # roll back one revision
```

---

## Configuration Reference

Values currently hardcoded in the source. Moving these to environment variables is on the roadmap.

| Value | Location | Current setting |
|---|---|---|
| `DATABASE_URL` | `.env` | *(required, no default)* |
| Vehicle A position | `vehicle_a_main.py` | `37.7750, -122.4190` (static) |
| H3 resolution | `vehicle_a_main.py` | `9` (~174 m edge) |
| AI scan interval | `vehicle_a_main.py` | `2.0` seconds |
| MQTT broker | both vehicle scripts | `broker.hivemq.com:8000`, WebSocket transport |
| Publish topic | `vehicle_a_main.py` | `intelligence/{h3_cell}/hazard` |
| Subscribe topic | `vehicle_b_reciever.py` | `intelligence/+/hazard` |
| Backend URL | `vehicle_b_reciever.py` | `http://localhost:8000/events` |
| VLM model | `vehicle_a_main.py` | `moondream` (swappable: `llava`, `paligemma`) |

Port `8000` is used for MQTT-over-WebSocket because raw MQTT port `1883` is frequently blocked on public and campus Wi-Fi.

---

## Known Limitations

We are documenting these openly rather than omitting them.

### Security

**There is no authentication of any kind.** Messages travel over a public, unauthenticated, unencrypted broker (`ws://`, not `wss://`). Any party who knows the topic structure can publish a fabricated `CRITICAL` alert that every listening vehicle will accept and act on. `vehicle_id` is a self-declared string with no verification, and there is no replay protection — a captured message can be rebroadcast indefinitely.

Production V2V solves this with IEEE 1609.2 certificates and rotating pseudonyms. Message signing and freshness checks are the highest-priority roadmap item.

The `POST /events` endpoint is likewise unauthenticated and unrated-limited.

### Perception

- **`confidence` is self-reported by the language model.** It is a generated token, not a calibrated probability, and should not be treated as a statistical measure of certainty.
- **Latency is 2–5 seconds per scan on CPU.** At 60 km/h that is 33–83 m of travel. DIVA is therefore suited to *persistent* hazards beyond sensor range — a stalled vehicle, debris, crash aftermath — and **not** to split-second collision avoidance.
- **A failed or truncated model response is silently dropped.** The code cannot currently distinguish "nothing detected" from "inference failed."
- **YOLOv8 is not yet in the pipeline.** `yolo_logic.py` is written but unused.

### Communication

- **The H3 geofilter is not yet enforced on the receiving side.** Vehicle A addresses its H3 cell correctly, but Vehicle B subscribes with a `+` wildcard and therefore accepts hazards from every cell on Earth. Distance-based filtering is not yet implemented.
- **Neighbouring cells are not covered.** Publishing to a single resolution-9 cell means a vehicle one cell behind — arguably the one that most needs the warning — will not match the topic once wildcard subscription is replaced with proper filtering. `h3.grid_disk` is required.
- **The system depends on a single public broker.** A "distributed" system routed through one third-party server is centralised in practice.

### State and data

- **No deduplication and no expiry.** The same stationary hazard is re-detected and re-broadcast every 2 seconds, producing repeated alerts and duplicate database rows for a single real-world event.
- **Vehicle position is static.** `CURRENT_LAT` / `CURRENT_LNG` are constants, so H3 cells never change during a run.
- **`timestamp` is stored in a timezone-naive column** while the pipeline generates timezone-aware UTC values; the offset is dropped on write.

### Engineering

- **No automated tests.**
- **Vehicle B does not act on alerts.** It displays and persists them; there is no fusion or decision logic.
- **The `vehicles` table is unused.**
- **`vehicle_b_reciever.py` is misspelled** and will be renamed.

---

## Roadmap

Ordered by priority. None of the following is implemented.

**Correctness and safety**
1. HMAC message signing and timestamp freshness checks to reject spoofed and replayed alerts.
2. Receiver-side geographic filtering; `h3.grid_disk` publishing to cover adjacent cells.
3. Deduplication with a time-to-live window so a single hazard produces a single alert.
4. Move inference off the render loop onto a worker thread.

**Perception**
5. Two-tier detection: YOLOv8n as a fast per-frame trigger (~20 ms), escalating to the VLM only when a candidate object appears. This is the intended role of the existing `yolo_logic.py`.
6. Live camera and GPS input in place of a static video file and fixed coordinates.
7. Explicit distinction between "scene clear" and "inference failed."

**Infrastructure**
8. Redis as a shared TTL memory layer for hazard state across vehicles.
9. RabbitMQ or a self-hosted MQTT broker with TLS and per-vehicle credentials.
10. Docker Compose for one-command setup.
11. Vehicle registration and heartbeat via the existing `vehicles` table and `/ws/{vehicle_id}` route.
12. All hardcoded configuration moved to environment variables.
13. Test suite covering schema validation, the API, and message routing.

**Longer term**
14. Multi-vehicle simulation with more than two nodes.
15. Relevance scoring and hazard prioritisation.
16. Real-world transport via C-V2X or DSRC / IEEE 802.11p.

---

## Team

| Member | Responsibility |
|---|---|
| **Abhishank** | Team Lead — MQTT and communication layer |
| **Aarit** | Backend and database |
| **Aniket** | Computer vision |
| **Antariksh** | Local LLM integration |
| **Agastaya** | Infrastructure (Redis, Docker — roadmap) |

---

## License

No license has been assigned yet. Until one is added, all rights are reserved and this code is provided for demonstration and evaluation purposes only.

---

*DIVA moves autonomous vehicles from isolated intelligence toward collaborative intelligence — from "every vehicle knows only what it can see" to "every vehicle benefits from what nearby vehicles have already seen."*
