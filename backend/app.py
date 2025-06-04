from flask import Flask, request, jsonify, abort, send_from_directory
from datetime import datetime
import os
import json

from models import insert_event  # Function to insert event into MongoDB
from db import events_collection  # MongoDB collection reference

app = Flask(__name__)

# Webhook Endpoint (POST /webhook)
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Check for valid JSON payload
        if not request.is_json:
            print("Invalid content-type:", request.content_type)
            abort(400, description="Invalid content-type, expected application/json")

        # Parse GitHub webhook payload
        data = request.get_json()
        event_type = request.headers.get('X-GitHub-Event')
        print("Event Type:", event_type)
        print("Raw Payload:", json.dumps(data, indent=2))  # for debugging

        payload = {}

        # Handle Push event
        if event_type == 'push':
            payload = {
                "author": data.get('pusher', {}).get('name', 'unknown'),
                "type": "push",
                "to_branch": data.get('ref', '').split('/')[-1],
                "timestamp": datetime.utcnow()
            }

        # Handle Pull Request and Merge events
        elif event_type == 'pull_request':
            action = data.get('action')
            pr = data.get('pull_request', {})

            # PR opened or reopened
            if action in ['opened', 'reopened']:
                payload = {
                    "author": pr.get('user', {}).get('login', 'unknown'),
                    "type": "pull_request",
                    "from_branch": pr.get('head', {}).get('ref', ''),
                    "to_branch": pr.get('base', {}).get('ref', ''),
                    "timestamp": datetime.utcnow()
                }

            # PR merged (merge event)
            elif action == 'closed' and pr.get('merged'):
                payload = {
                    "author": pr.get('user', {}).get('login', 'unknown'),
                    "type": "merge",
                    "from_branch": pr.get('head', {}).get('ref', ''),
                    "to_branch": pr.get('base', {}).get('ref', ''),
                    "timestamp": datetime.utcnow()
                }
            else:
                return '', 204  # PR closed but not merged → ignore

        else:
            return '', 204  # Unsupported event type

        # Save the event in MongoDB
        insert_event(payload)
        return '', 200

    except Exception as e:
        print("Webhook Error:", str(e))
        return 'Error processing webhook', 400



# Events API (GET /events)

@app.route('/events', methods=['GET'])
def get_events():
    # Get last 10 events sorted by timestamp (latest first)
    events = events_collection.find().sort("timestamp", -1).limit(10)
    result = []

    for e in events:
        event = {
            "author": e["author"],
            "type": e["type"],
            "timestamp": e["timestamp"].isoformat(),  # ISO string for frontend parsing
        }
        if e["type"] == "push":
            event["to_branch"] = e["to_branch"]
        elif e["type"] in ["pull_request", "merge"]:
            event["from_branch"] = e["from_branch"]
            event["to_branch"] = e["to_branch"]
        result.append(event)

    return jsonify(result)
    
# Serve Frontend (GET /)
@app.route('/')
def index():
    # Serve the main frontend HTML file
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'index.html')

@app.route('/script.js')
def script():
    # Serve the frontend JavaScript file
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'script.js')

