import os
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

headers = {
    "Authorization": f"Bearer {os.getenv("NOTION_SECRET")}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03",
}
base_url = "https://api.notion.com/v1"

@csrf_exempt
def notion_test(request):
    BLOCK_ID = "26c968085ab980c093f1eb8c6ae500bb"

    url = f"{base_url}/blocks/{BLOCK_ID}/children"

    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        print("✅ Success!")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)

    return JsonResponse(resp.json(), status=200)

@csrf_exempt
def update_stock(request):
    if request.method != "PATCH":
        return JsonResponse({"error": "PATCH only"}, status=405)

    BLOCK_ID = "26c96808-5ab9-80a2-8294-c9762de03fb1"

    url = f"{base_url}/blocks/{BLOCK_ID}"

    data = json.loads(request.body)
    payloads = {
        "table_row": {
            "cells": [
                [
                    {
                        "type": "text",
                        "text": {
                            "content": data.get("content")
                        }
                    }
                ],
                [
                    {
                        "type": "text",
                        "text": {
                            "content": data.get("content")
                        }
                    }
                ],
                [
                    {
                        "type": "text",
                        "text": {
                            "content": data.get("content")
                        }
                    }
                ]
            ]
        }
    }

    try:
        resp = requests.patch(url, headers=headers, timeout=10, json=payloads)
        resp.raise_for_status()
        print("✅ Success!")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)

    return JsonResponse(resp.json(), status=200)