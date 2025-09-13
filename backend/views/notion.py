import os
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

headers = {
    "Authorization": f"Bearer {os.getenv("NOTION_SECRET")}",
    "Content-Type": "application/json",
    "Notion-Version": f"{os.getenv("NOTION_VERSION")}",
}
base_url = "https://api.notion.com/v1"

@csrf_exempt
def update_stock(request):
    if request.method != "PATCH":
        return JsonResponse({"error": "PATCH only"}, status=405)

    block_id = os.getenv("STOCK_TABLE_ID")
    details = get_details(block_id)

    url = f"{base_url}/blocks/{block_id}"

    data = json.loads(request.body)
    payload = {
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
        resp = requests.patch(url, headers=headers, timeout=10, json=payload)
        resp.raise_for_status()
        print("✅ Success!")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)

    return JsonResponse(resp.json(), status=200)

def get_details(block_id):
    try:
        resp = requests.get(f"{base_url}/blocks/{block_id}/children", headers=headers, timeout=10)
        resp.raise_for_status()
        print("✅ Success!")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)

    return resp.json()