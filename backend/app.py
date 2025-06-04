from flask import Flask, request, jsonify
from datetime import datetime
from models import insert_event
from db import events_collection

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    from datetime import datetime
    import json
    from flask import abort

    try:
        if not request.is_json:
            print("Invalid content-type:", request.content_type)
            abort(400, description="Invalid content-type, expected application/json")

        data = request.get_json()
        event_type = request.headers.get('X-GitHub-Event')
        print("Event Type:", event_type)
        print("Raw Payload:", json.dumps(data, indent=2))

        payload = {}

        if event_type == 'push':
            payload = {
                "author": data.get('pusher', {}).get('name', 'unknown'),
                "type": "push",
                "to_branch": data.get('ref', '').split('/')[-1],
                "timestamp": datetime.utcnow()
            }

        elif event_type == 'pull_request':
            action = data.get('action')
            pr = data.get('pull_request', {})
            if action in ['opened', 'reopened']:
                payload = {
                    "author": pr.get('user', {}).get('login', 'unknown'),
                    "type": "pull_request",
                    "from_branch": pr.get('head', {}).get('ref', ''),
                    "to_branch": pr.get('base', {}).get('ref', ''),
                    "timestamp": datetime.utcnow()
                }
            elif action == 'closed' and pr.get('merged'):
                payload = {
                    "author": pr.get('user', {}).get('login', 'unknown'),
                    "type": "merge",
                    "from_branch": pr.get('head', {}).get('ref', ''),
                    "to_branch": pr.get('base', {}).get('ref', ''),
                    "timestamp": datetime.utcnow()
                }
            else:
                return '', 204
        else:
            return '', 204

        from models import insert_event
        insert_event(payload)
        return '', 200

    except Exception as e:
        print("Webhook Error:", str(e))
        return 'Error processing webhook', 400



@app.route('/events', methods=['GET'])
def get_events():
    from db import events_collection
    events = events_collection.find().sort("timestamp", -1).limit(10)
    result = []
    for e in events:
        event = {
            "author": e["author"],
            "type": e["type"],
            "timestamp": e["timestamp"].isoformat(),
        }
        if e["type"] == "push":
            event["to_branch"] = e["to_branch"]
        elif e["type"] == "pull_request":
            event["from_branch"] = e["from_branch"]
            event["to_branch"] = e["to_branch"]
        elif e["type"] == "merge":
            event["from_branch"] = e["from_branch"]
            event["to_branch"] = e["to_branch"]
        result.append(event)
    return jsonify(result)


from flask import send_from_directory
import os

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'index.html')

@app.route('/script.js')
def script():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'script.js')

