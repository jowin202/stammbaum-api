from fastapi import FastAPI, HTTPException
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
app.include_router(person.router, tags=["Personen"], prefix="/api/personen")
