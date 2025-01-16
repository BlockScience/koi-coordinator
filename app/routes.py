import httpx
from rid_lib.ext import Event, EventType
from rid_lib.ext.utils import json_serialize
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from secrets import token_urlsafe
from .core import cache, subscriber, publisher
from .auth import api_key_header
from .models import SubscriberProfile, SubscriptionType

subscriber_queue = {}

router = APIRouter(
    dependencies=[Depends(api_key_header)]
)

def notify_subscribers(events: list[Event]):
    for event in events:
        sub_ids = subscriber.lookup.get(event.rid.context)
        if not sub_ids: continue
        
        for sub_id in sub_ids:
            sub_profile = subscriber.profiles[sub_id]
    
            queue = subscriber_queue.setdefault(sub_id, [])
            queue.append(event)
            
    print(subscriber_queue)
    
    for sub_id, events in subscriber_queue.items():
        sub_profile = subscriber.profiles[sub_id]
        
        if sub_profile.sub_type == SubscriptionType.WEBHOOK:
            try:
                httpx.post(sub_profile.url, json=[
                    event.to_json() for event in queue
                ])
                queue.clear()
            except httpx.ConnectError:
                print("failed to connect", queue)
                continue
    

@router.post("/events/publish")
async def publish_event(events: list[Event], background_tasks: BackgroundTasks):
    for event in events:
        if event.event_type in (EventType.NEW, EventType.UPDATE):
            cache.write_manifest_only(event.rid, event.manifest)
        elif event.event_type == EventType.FORGET:
            cache.delete(event.rid)
            
    background_tasks.add_task(
        notify_subscribers, events
    )
                            
                    
@router.get("/events/poll/{sub_id}")
async def poll_events(sub_id: str):
    if sub_id not in subscriber_queue:
        raise HTTPException(
            status_code=404,
            detail="Subscriber ID not found"
        )

    queue = subscriber_queue[sub_id]
    events_json = [
        event.to_json() for event in queue
    ]
    queue.clear()
    return events_json 


@router.post("/events/subscribe/{sub_id}")
@router.post("/events/subscribe")
async def subscribe_to_events(sub_profile: SubscriberProfile, sub_id: str = None):
    if sub_id is None:
        sub_id = token_urlsafe(16)

    subscriber.set_profile(sub_id, sub_profile)
    
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