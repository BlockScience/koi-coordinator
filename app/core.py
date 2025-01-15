from fastapi import FastAPI
from rid_lib.ext import Cache

server = FastAPI()
cache = Cache("cache")

from .routes import router

server.include_router(router)