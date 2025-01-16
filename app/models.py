from pydantic.dataclasses import dataclass
from enum import StrEnum


@dataclass
class PublisherProfile:
    url: str
    contexts: list[str]


class SubscriptionType(StrEnum):
    POLL = "poll"
    WEBHOOK = "webhook"

@dataclass
class SubscriberProfile:
    sub_type: SubscriptionType
    contexts: list[str]
    url: str | None = None