from db import events_collection

def insert_event(payload):
    events_collection.insert_one(payload)
