# GHOST PROTOCOL

> *Anonymous. Untraceable. Inevitable.*

A browser-based MMO hacking simulation where psychological pressure, operational security, and real consequences define your survival.

---

## Architecture

```
ghost-protocol/
├── backend/          FastAPI + PostgreSQL + Redis + Neo4j
│   ├── app/
│   │   ├── models/   SQLAlchemy ORM (Player, Operation, Heat, Prison…)
│   │   ├── services/ Business logic (14 service modules)
│   │   ├── routers/  API routes (14 router modules)
│   │   ├── data/     Game constants, skill trees, factions
│   │   └── main.py   FastAPI app + lifespan + background tasks
│   ├── alembic/      Database migrations
│   └── tests/        pytest test suite
├── frontend/         React 18 + TypeScript + xterm.js + D3.js
│   └── src/
│       ├── components/ Terminal, TraceGraph, HUD, Notifications
│       ├── pages/      Login, Register, MainTerminal + panels
│       ├── services/   API client, WebSocket, Command router
│       └── store/      Zustand global state
├── scripts/
│   └── smoke_test.sh  End-to-end curl test suite
└── docker-compose.yml Full stack: backend, frontend, postgres, redis, neo4j
```

---

## Quickstart

### Prerequisites
- Docker + Docker Compose
- (Optional) Python 3.12 + Node 20 for local dev

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and ANTHROPIC_API_KEY at minimum
```

### 2. Start everything

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Neo4j browser: http://localhost:7474

### 3. Run migrations

```bash
docker compose exec backend alembic upgrade head
```

The backend seeds 50 world nodes and NPC market listings on first startup automatically.

### 4. Smoke test

```bash
./scripts/smoke_test.sh
```

### Local backend dev

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.development .env
uvicorn app.main:app --reload --port 8000
```

### Local frontend dev

```bash
cd frontend
npm install
npm run dev   # Proxies /api and /ws to localhost:8000
```

---

## Game Systems

### Operations (4-phase)
Every operation progresses through: **RECON → EXPLOIT → PERSIST → MONETIZE**

Each phase is an independent probability roll influenced by skill level, device quality, node vulnerability, alert state, and your psychological state.

### Heat & Threat Tiers
Five independent heat domains (local_leo, federal, intelligence, corporate, rivals) each with different decay rates. Total heat determines your threat tier:

| Tier | Name | Heat Range |
|------|------|-----------|
| 1 | Off The Radar | 0–20 |
| 2 | Persons of Interest | 21–40 |
| 3 | Active Inquiry | 41–60 |
| 4 | Manhunt | 61–80 |
| 5 | Arrest Probable | 81–100 |

**Tier 5 + phase failure = arrest.** Use `go-dark` to accelerate decay at the cost of inactivity.

### Psychological State
Seven variables updated after every operation:
- **Stress** → reduces success rates
- **Sleep Debt** → reduces focus
- **Paranoia** → causes hallucinations above 80
- **Ego** → success bonus/penalty
- **Burnout** → general degradation
- **Trust Index** → faction interaction quality
- **Focus** → derived: `100 - (stress×0.3) - (sleep_debt×0.4) - (burnout×0.3)`

### Skill Trees (6)
Social, Exploitation, Cryptography, Hardware, Counterintel, Economics.
Each has 5 tiers with abilities unlocking at levels 1/10/20/35/45.

### Factions (5)
The Collective, Black Array, Sovereign Shield, Signal Zero, Freenode.
Each requires specific reputation and operation types to unlock contact.

---

## Terminal Commands

```
help              Full command reference
status            Player vitals overview
nodes             Accessible target list
scan <node_key>   Target intelligence report
op start <node> <device> [approach]  Launch operation
op advance        Execute current phase
op abort          Emergency abort (50% XP)
heat              Heat status by domain
go-dark <hours>   Accelerate heat decay
wallet            Balance summary
market            Browse black market
launder <amount>  Convert crypto to privacy coin
skills            Skill tree overview
factions          Faction standings
```

---

## API Reference

Full interactive docs at `/docs` (Swagger) and `/redoc`.

Auth: `POST /api/v1/auth/register` → `POST /api/v1/auth/login` → use `Authorization: Bearer <token>`

WebSocket: `ws://localhost:8000/ws/{player_id}?token=<token>` — receives real-time heat, operation, and world events.

---

## Testing

```bash
cd backend
pytest tests/ -v --tb=short
```

Test coverage: auth, operations, heat, economy, skills.

---

## Phase Status

- [x] **Phase 0** — Terminal Python prototype *(validated fun)*
- [x] **Phase 1** — Foundation, single-player web *(this build)*
- [ ] Phase 2 — MMO layer, multiplayer
- [ ] Phase 3 — Depth systems
- [ ] Phase 4 — World-class polish
- [ ] Phase 5 — Living world

---

*Build the ghost. Don't get caught.*
