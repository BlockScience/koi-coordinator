import json
from dataclasses import asdict
from .models import PublisherProfile, SubscriberProfile


class SimpleStorage:
    profiles: dict[str, SubscriberProfile | PublisherProfile]
    lookup: dict[str, list[str]]
    
    def __init__(
        self, 
        file_path: str, 
        profile_type: SubscriberProfile | PublisherProfile
    ):
        self.file_path = file_path
        self.profile_type = profile_type
        self.profiles, self.lookup = self._read() or ({}, {})
    
    def _read(self):
        try:
            with open(self.file_path, "r" ) as f:
                data = json.load(f)
                profiles = {
                    k: self.profile_type(**v) 
                    for k, v in data["profiles"].items()
                }
                lookup = data["lookup"]
                
                return profiles, lookup
                            
        except FileNotFoundError:
            return None
        
    def _write(self):
        with open(self.file_path, "w") as f:
            json.dump({
                "profiles": {
                    k: asdict(v) 
                    for k, v in self.profiles.items()
                },
                "lookup": self.lookup
            }, f, indent=2)
    
    def set_profile(self, id, profile: PublisherProfile | SubscriberProfile):
        prev_profile = self.profiles.get(id)
        if prev_profile:
            for ctx in prev_profile.contexts:
                self.lookup[ctx].remove(id)
        
        self.profiles[id] = profile
        
        for ctx in profile.contexts:
            self.lookup.setdefault(ctx, []).append(id)
            
        self._write()
            
