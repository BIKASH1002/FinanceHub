import json
import uuid
import secrets
from datetime import datetime, timedelta
from django.utils import timezone

def get_response_format():
    
    response = {}
    response["success"] = None
    response["data"] = {}
    response["meta"] = {}
    response["errors"] = []
    response["error_code"] = None
    
    return response


def convert_data(data):
    
    try:
        post_data = data.decode('utf8')
        post_data = json.loads(post_data)
    except Exception:
        post_data = None
    return post_data
