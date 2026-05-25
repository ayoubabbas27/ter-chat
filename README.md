# ter-chatbot

Natural language → Gorgias Prolog, with syntax validation and Gorgias Cloud testing.

## Project layout

```
backend/             # Python API + .env (secrets)
frontend/            # React UI
docker-compose.yml
```

## Run the app

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) with Compose.

1. Create your env file (first time only):

```bash
cp backend/.env.example backend/.env
# edit backend/.env — ANTHROPIC_API_KEY, GORGIAS_USER, etc.
```

2. Start everything (logs stream in this terminal; press `Ctrl+C` to stop):

```bash
docker compose up --build
```

To run in the background and follow logs separately:

```bash
docker compose up --build -d
docker compose logs -f
```

3. Open **http://localhost:5173**

The UI proxies `/api` to the backend inside Docker. The API is also exposed on **http://localhost:8080** (host port 8080 → container 8000, so it does not conflict with a local process on port 8000).

Stop with `Ctrl+C` or:

```bash
docker compose down
```