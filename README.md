# DIVA
## Distributive Intelligence for Vehicle Automativity

DIVA is a distributed AI system for Vehicle-to-Vehicle (V2V) communication, designed to enable autonomous vehicles to share meaningful environmental information with nearby vehicles.

Instead of transmitting raw camera feeds between vehicles, DIVA allows each vehicle to process its own surroundings locally and communicate compact semantic information such as detected hazards, confidence levels, positions, and recommended actions.

The goal is to demonstrate how distributed intelligence can make autonomous vehicles safer, faster, and more efficient by allowing vehicles to collectively understand their surroundings.

---

## 🚗 Core Idea

Traditional autonomous vehicles primarily rely on their own sensors and perception systems.

DIVA introduces another layer:
```
Vehicle A
    ↓
Local AI Perception
    ↓
Semantic Message
    ↓
V2V Communication
    ↓
Vehicle B
    ↓
Local Decision Making
```

For example, Vehicle A may detect an overturned truck around a blind corner.

Instead of sending the entire camera feed, Vehicle A can send:
```
{
    "vehicle_id": "vehicle_A",
    "event_type": "hazard",
    "object_type": "overturned_truck",
    "confidence": 0.92,
    "risk_level": "HIGH",
    "position": {
        "latitude": 28.6139,
        "longitude": 77.209
    },
    "description": "Overturned truck blocking the road",
    "recommendation": "Reduce speed and change lane if safe"
}
```

Vehicle B can then use this information to react before the hazard becomes visible to its own sensors.

---

## 🧠 Why Distributed Intelligence?

A vehicle does not need to independently perceive everything around it.

Nearby vehicles can act as additional sources of perception.

This creates a distributed intelligence system where:

- Each vehicle processes its own sensor data.
- Vehicles exchange semantic information.
- Important information can reach vehicles outside direct line-of-sight.
- Bandwidth requirements are significantly lower than transmitting raw video.
- Vehicles can collectively build a better understanding of their surroundings.

---

## 🏗️ System Architecture

DIVA is designed as a modular distributed architecture.

### Vehicle Layer

Each vehicle contains:

- Camera / sensor input
- Local perception model
- Semantic message generation
- V2V communication client
- Local memory
- Decision-making logic

### Communication Layer

The prototype supports communication between vehicles using messaging and persistent connections.

Current components include:

- FastAPI
- WebSockets
- RabbitMQ
- Redis

### Backend Layer

The backend provides:

- Vehicle connections
- Semantic event reception
- Message broadcasting
- Event persistence
- Vehicle state management
- Communication APIs

### Database Layer

PostgreSQL is used for persistent storage through SQLAlchemy and Alembic.

The database stores structured information such as:

- Vehicles
- Detected events
- Semantic messages
- Event metadata

---

## 🔄 Communication Pipeline

The current prototype follows this general pipeline:
```
Camera / Video
        ↓
Local Perception
        ↓
Semantic Event
        ↓
FastAPI Backend
        ↓
Message Broker
        ↓
Target Vehicle
        ↓
Redis Memory
        ↓
Decision
```

The important design principle is that vehicles exchange **semantic information rather than raw sensor data**.

---

## 📡 V2V Communication

For the prototype, communication can be demonstrated using two laptops representing two vehicles.

### Vehicle A

Vehicle A processes a video and detects an event.

Example:

Vehicle A
    ↓
Hazard detected
    ↓
Semantic message generated
    ↓
Message sent
    ↓
Vehicle B

### Vehicle B

Vehicle B receives the semantic message and can use it to make an informed decision.

Example:

Received:

Hazard: pedestrian
Confidence: 0.96
Recommendation: slow_down

Vehicle B can then incorporate this information into its local decision-making process.

---

## ⚡ Redis

Redis is used as a fast temporary memory layer.

Vehicle-specific memories can be stored using keys such as:

vehicle:A:memory:pedestrian

vehicle:B:memory:pothole

Each memory can have a TTL so that outdated hazards automatically expire.

This is important because road conditions are dynamic.

For example:

Hazard detected
        ↓
Stored in Redis
        ↓
Vehicle uses information
        ↓
Memory expires after TTL
        ↓
Stale information removed

This prevents old hazards from remaining permanently active.

---

## 🐇 RabbitMQ

RabbitMQ is used as the messaging layer in the distributed communication architecture.

The prototype uses a topic exchange:

vehicle_topics

Vehicles can communicate using routing keys such as:

to.A

to.B

This allows messages to be directed toward specific vehicles while maintaining a scalable messaging architecture.

---

## 🔌 FastAPI Backend

The backend is implemented using FastAPI.

Important endpoints include:

GET /health

Used to verify that the backend is running.

POST /events

Used to receive semantic events.

WebSocket:

/ws/{vehicle_id}

Used for persistent vehicle connections and real-time communication.

Example:

Vehicle A
    ↓
WebSocket
    ↓
Backend
    ↓
Broadcast / routing
    ↓
Vehicle B

---

## 🗄️ PostgreSQL

PostgreSQL provides persistent storage for information that should survive beyond the lifetime of a Redis memory entry.

The project uses:

- PostgreSQL
- SQLAlchemy
- Alembic

Alembic manages database schema migrations.

For example:

Python SQLAlchemy Models
        ↓
Alembic Migration
        ↓
PostgreSQL

---

## 🤖 AI Layer

The AI layer is responsible for converting raw sensor information into meaningful semantic information.

The intended pipeline is:

Video
  ↓
Object / Scene Detection
  ↓
AI Reasoning
  ↓
Semantic Event
  ↓
V2V Message

The system is designed to support local AI processing so that vehicles do not need to continuously upload raw video to a central server.

---

## 🧩 Semantic Communication

One of the main ideas behind DIVA is semantic communication.

Instead of transmitting:

10 MB video

the vehicle transmits something closer to:

{
    "hazard": "accident",
    "confidence": 0.94,
    "risk": "HIGH",
    "recommendation": "slow_down"
}

This drastically reduces the amount of information that needs to be transmitted while preserving the information that matters for decision making.

---

## 🧪 Current Demo

The planned demonstration uses two laptops.

### Laptop A

Represents Vehicle A.

It:

1. Processes a video.
2. Detects an environmental event.
3. Generates a semantic message.
4. Sends the message through the communication layer.

### Laptop B

Represents Vehicle B.

It:

1. Receives the semantic message.
2. Stores relevant information in temporary memory.
3. Displays the received hazard.
4. Uses the information for a local decision.

This demonstrates distributed perception without requiring two physical autonomous vehicles.

---

## 📁 Project Structure
```
backend/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── core/
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── vehicle.py
│   │   └── event.py
│   │
│   ├── schemas/
│   │   └── semantic_message.py
│   │
│   ├── websocket/
│   │   ├── handlers.py
│   │   └── manager.py
│   │
│   └── main.py
│
├── tests/
│
└── requirements.txt
```
Additional components such as AI inference, Redis, RabbitMQ, and vehicle clients can be organized as separate modules as the system develops.

---

## 🛠️ Technologies

### Backend

- Python
- FastAPI
- Uvicorn

### AI

- Computer Vision
- Local AI inference
- Gemma / LLM-based reasoning

### Communication

- WebSockets
- RabbitMQ
- MQTT where required

### Memory

- Redis

### Database

- PostgreSQL
- SQLAlchemy
- Alembic

### Development

- Git
- GitHub
- VS Code

---

## 🚀 Getting Started

Clone the repository:
```
git clone https://github.com/AaritShrama/Distributed-AI-System-For-V2V-Communication.git
```
Move into the project:
```
cd Distributed-AI-System-For-V2V-Communication
```
Create a virtual environment:
```
python -m venv .venv
```
Activate it on Windows:
```
.venv\Scripts\activate
```
Install dependencies:
```
pip install -r requirements.txt
```
---

## ⚙️ Environment Variables

Create a `.env` file in the project root.

Example:
```
DATABASE_URL=postgresql://username:password@host:5432/database
```
---

## ▶️ Running the Backend

From the project root:
```
python -m uvicorn backend.app.main:app --reload
```
The backend should then be available at:
```
http://127.0.0.1:8000
```
FastAPI documentation:
```
http://127.0.0.1:8000/docs
```
Health check:
```
GET /health
```
---

## 🗃️ Database Migrations

Create a migration after modifying SQLAlchemy models:

alembic revision --autogenerate -m "description"

Apply migrations:

alembic upgrade head

Rollback the latest migration:

alembic downgrade -1

---

## 🎯 Project Goals

The long-term goal of DIVA is to demonstrate how autonomous vehicles can cooperate through distributed AI.

Key objectives include:

- Reduce communication bandwidth.
- Share only useful semantic information.
- Enable real-time V2V communication.
- Maintain temporary vehicle memories.
- Improve situational awareness.
- Support decentralized decision making.
- Reduce dependence on centralized AI processing.
- Create a scalable architecture suitable for future autonomous vehicle networks.

---

## 🔮 Future Development

Planned improvements include:

- Gemma integration for semantic reasoning.
- Real-time video processing.
- YOLO / computer vision perception.
- Complete Vehicle A → Vehicle B pipeline.
- Redis-based contextual memory.
- RabbitMQ-based message routing.
- MQTT-based vehicle communication experiments.
- Multi-vehicle communication.
- Vehicle prioritization and routing.
- Event expiry and relevance scoring.
- Cloud-hosted database infrastructure.
- Real-world V2V communication using automotive communication standards.
- Simulation using multiple virtual vehicles.

---

## 🌐 Real-World Deployment

The two-laptop demonstration is only a prototype representation of the communication architecture.

In a real vehicle, the same semantic messages could be transmitted using automotive communication technologies such as:

- C-V2X
- DSRC / IEEE 802.11p
- 5G networks
- Wi-Fi-based communication for testing

The important abstraction remains the same:
```
Vehicle Sensor
      ↓
Local AI
      ↓
Semantic Representation
      ↓
V2V Network
      ↓
Nearby Vehicle
      ↓
Local AI Decision
```
---

## 👥 Team

### Aarit

Backend and Database Setup

### Abhishank

Team Lead, MQTT and Communication Setup

### Agastaya

Redis and Docker

### Aniket

Computer Vision

### Antariksh

Local LLM Setup

---

## 🏁 Vision

DIVA aims to move autonomous vehicles from isolated intelligence toward collaborative intelligence.

Instead of:

"Every vehicle knows only what it can see."

DIVA aims for:

"Every vehicle can benefit from what other vehicles have already learned."

Distributed perception.
Shared intelligence.
Safer mobility.

---

## 📜 License

This project is currently developed as a research and prototype system.
