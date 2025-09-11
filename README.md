# fs-backend

A minimal FastAPI backend.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

### Installation & Running

1.  Clone the repository:
```bash
git clone <repository-url>
cd fs-backend
```

2.  Install dependencies:
```bash
uv sync
```

3.  Run the application:
```bash
uv run fastapi dev --port 3001 src/main.py
```

The application will be available at `http://127.0.0.1:3001`.
