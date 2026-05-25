# DataFlow API

Production-ready FastAPI backend for DataFlow Pipeline Configuration Platform.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Initialize DB

```bash
python -m database.init_db
```

## Test

```bash
pytest -q
```

## Seed/Usage

1. Start API
2. Open `/docs`
3. Create connection (`POST /api/v1/connections`)
4. Create pipeline config (`POST /api/v1/pipeline-configs`)
5. Create audit run (`POST /api/v1/audit/runs`)
