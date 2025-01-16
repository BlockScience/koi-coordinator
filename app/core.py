from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from rid_lib.ext import Cache

server = FastAPI()
cache = Cache("cache")

from .routes import router

server.include_router(router)

@server.get("/", response_class=PlainTextResponse)
async def home():
    return "this is a experimental KOI coordinator"