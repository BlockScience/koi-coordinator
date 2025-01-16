from fastapi import FastAPI
from rid_lib.ext import Cache
from .storage import SimpleStorage
from .models import SubscriberProfile, PublisherProfile

server = FastAPI()
cache = Cache("cache")
subscriber = SimpleStorage("sub.json", SubscriberProfile)
publisher = SimpleStorage("pub.json", PublisherProfile)

from .routes import router
server.include_router(router)