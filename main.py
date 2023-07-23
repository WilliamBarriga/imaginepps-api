# Starlette
from starlette.middleware.cors import CORSMiddleware

# FastAPI
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer

# Routers
from users.router import api_router as users_router
from auth.router import api_router as auth_router
from notes.router import api_router as notes_router

# db
from imagine.db_manager import db, rd

# Middleware
from imagine.middleware import LogsMiddleware

# Env
from decouple import config, Csv

app = FastAPI(
    title="Imagine API",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config("CORS_ORIGINS", cast=Csv(), default="*"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LogsMiddleware)


@app.on_event("startup")
def startup_event():
    print("*" * 20, flush=True)
    print("Starting up...", flush=True)
    print("connecting to db...", flush=True)
    db.fetch_one("SELECT 1")
    print("connected to db...", flush=True)
    print("connecting to redis...", flush=True)
    rd.conn.ping()
    print("connected to redis...", flush=True)
    print("*" * 20, flush=True)


@app.on_event("shutdown")
def shutdown_event():
    print("*" * 20, flush=True)
    print("Shutting down...", flush=True)
    print("*" * 20, flush=True)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(notes_router)
