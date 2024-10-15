import logging

from .routers.binaries import archs
from .models import create_db_and_tables

from fastapi import Depends, FastAPI

app = FastAPI()
log = logging.getLogger(__name__)


app.include_router(archs.router)


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"message": "Hello, I'm Chacra!"}
