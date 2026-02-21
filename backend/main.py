from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from contextlib import asynccontextmanager
import db
from db import initialize_connection_pool, pg_db_init
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_is_ready = False

    while not db_is_ready:
        try:
            print("Waiting for DB...", flush=True)
            await initialize_connection_pool()
            await pg_db_init()
            db_is_ready = True
            print("DB ready!", flush=True)
        except Exception as e:
            print(f"DB not ready yet: {e}", flush=True)
            await asyncio.sleep(1)

    yield


app = FastAPI(title="Personen-Stammbaum API", lifespan=lifespan)


from routes import person
from routes import stammbaum
app.include_router(person.router, tags=["Personen"], prefix="/api/personen")
app.include_router(stammbaum.router, tags=["Stammbaum"], prefix="/api/stammbaum")




app.mount("/", StaticFiles(directory="static", html=True), name="static-root")

@app.middleware("http")
async def spa_fallback(request: Request, call_next):

    # Paths that should NOT fall back to index.html
    passthrough_prefixes = (
        "/api", "/checkout", "/docs", "/redoc", "/openapi.json"
    )
    if (
        request.url.path.startswith(passthrough_prefixes)
        or os.path.isfile(f"static{request.url.path}")
    ):
        return await call_next(request)

    # For anything else, serve index.html
    with open("static/index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
