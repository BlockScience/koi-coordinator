import httpx
from rid_lib.ext import Event, EventType
from rid_lib.ext.utils import json_serialize
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from secrets import token_urlsafe
from .core import cache, subscriber, publisher
from .auth import api_key_header
from .models import SubscriberProfile, SubscriptionType, PublisherProfile

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
    

@router.post("/events/publish/{pub_id}")
async def publish_event(pub_id: str, events: list[Event], background_tasks: BackgroundTasks):
    if pub_id not in publisher.profiles:
        raise HTTPException(
            status_code=404,
            detail="Pubscriber ID not found"
        )
        
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
    if sub_id not in subscriber.profiles:
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


@router.get("/profiles/subscriber/{sub_id}")
async def get_subscriber_profile(sub_id: str):
    return subscriber.profiles.get(sub_id)

@router.post("/profiles/subscriber/{sub_id}")
@router.post("/profiles/subscriber")
async def set_subscriber_profile(sub_profile: SubscriberProfile, sub_id: str = None):
    if sub_id is None:
        sub_id = token_urlsafe(16)

    subscriber.set_profile(sub_id, sub_profile)
    
    return {
        "sub_id": sub_id
    }
    
@router.get("/profiles/publisher/{pub_id}")
async def get_publisher_profile(pub_id: str):
    return publisher.profiles.get(pub_id)

@router.get("/profiles/publisher")
async def get_publishers_by_context(context: str):
    return [
        publisher.profiles[pub_id]
        for pub_id in publisher.lookup.get(context, [])
    ]

@router.post("/profiles/publisher/{pub_id}")
@router.post("/profiles/publisher")
async def set_subscriber_profile(pub_profile: PublisherProfile, pub_id: str = None):
    if pub_id is None:
        pub_id = token_urlsafe(16)

    publisher.set_profile(pub_id, pub_profile)
    
    return {
        "pub_id": pub_id
    }    
    




@router.get("/rids")
async def retrieve_rids():
    return json_serialize(cache.read_all_rids())

@router.get("/manifests")
async def retrieve_manifests():
    return json_serialize([
        cache.read(rid).manifest for rid in cache.read_all_rids()
    ])