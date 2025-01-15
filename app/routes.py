from enum import StrEnum
import httpx
from rid_lib.ext import Event, EventType
from rid_lib.ext.utils import json_serialize
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from secrets import token_urlsafe
from .core import cache
from .auth import api_key_header

router = APIRouter(
    dependencies=[Depends(api_key_header)]
)

subscribers = {}
subscribers_queue = {}

@router.post("/events/publish")
async def publish_event(event: Event):
    if event.event_type in (EventType.NEW, EventType.UPDATE):
        cache.write_manifest_only(event.rid, event.manifest)
    elif event.event_type == EventType.FORGET:
        cache.delete(event.rid)
        
    print(subscribers)
                
    for sub in subscribers.values():
        print(sub)
        if event.rid.context in sub["contexts"]:
            queue = subscribers_queue.setdefault(sub["id"], [])
            queue.append(event.to_json())
        
            if sub["type"] == SubscriptionType.WEBHOOK:
                try:
                    while queue:
                        httpx.post(sub["webhook"], json=queue[-1])
                        queue.pop()
                except httpx.ConnectError:
                    print("failed to connect", queue)
                    continue
                    
@router.get("/events/poll/{sub_id}")
async def poll_events(sub_id: str):
    global subscribers_queue
    if sub_id not in subscribers_queue:
        raise HTTPException(
            status_code=404,
            detail="Subscriber ID not found"
        )
    
    queued_events = subscribers_queue[sub_id]
    subscribers_queue[sub_id] = []
    return queued_events


class SubscriptionType(StrEnum):
    POLL = "poll"
    WEBHOOK = "webhook"

class Subscription(BaseModel):
    type: SubscriptionType
    webhook: str | None = None
    contexts: list[str]

@router.post("/events/subscribe/{sub_id}")
@router.post("/events/subscribe")
async def subscribe_to_events(subscription: Subscription, sub_id: str = None):
    if sub_id is None:
        sub_id = token_urlsafe(16)
    
    sub_dict = subscription.model_dump()
    sub_dict["id"] = sub_id
    
    print(sub_dict)
    
    subscribers[sub_id] = sub_dict
    
    return {
        "sub_id": sub_id
    }
    
@router.get("/rids")
async def retrieve_rids():
    return json_serialize(cache.read_all_rids())

@router.get("/manifests")
async def retrieve_manifests():
    return json_serialize([
        cache.read(rid).manifest for rid in cache.read_all_rids()
    ])