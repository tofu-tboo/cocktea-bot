import os, json, unicodedata, random, re
from urllib.parse import unquote
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .dto.notion_dto import BlockDetail, Block, TableRow, RichText, Text, Annotations
from .dto.table_dto import StockTableRow, Ingredient, RecipeTableRow

headers = {
    "Authorization": f"Bearer {os.getenv("NOTION_SECRET")}",
    "Content-Type": "application/json",
    "Notion-Version": f"{os.getenv("NOTION_VERSION")}",
}
base_url = "https://api.notion.com/v1"

@csrf_exempt
def get_recipe(request, cocktail_name):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    block_id = os.getenv("RECIPE_TABLE_ID")
    details = BlockDetail.model_validate_json(get_details(block_id).text)
    cocktail_name = unicodedata.normalize("NFC", unquote(cocktail_name))

    
    if details.object != "list":
        return JsonResponse({"message": "관리자에게 문의하세요. (Not a List)"}, status=500)
    elif len(details.results) == 0:
        return JsonResponse({"message": "관리자에게 문의하세요. (Empty List)"}, status=500)

    recipe = None
    ingredients = None
    filtered_results = [block for block in details.results if block.type == "table_row" and block.table_row is not None]
    if len(filtered_results) == 0:
        return JsonResponse({"message": "관리자에게 문의하세요. (No Table Rows)"}, status=500)
    filtered_results.pop(0) # 첫번째 행은 헤더이므로 제거
    
    if cocktail_name in ["아무거나", "랜덤", "random", "뽑기"]:
        random.shuffle(filtered_results)
        recipe = filtered_results[0].table_row.cells[1][0].plain_text
        ingredients = filtered_results[0].table_row.cells[2][0].plain_text
        cocktail_name = filtered_results[0].table_row.cells[0][0].plain_text
    else:
        for block in filtered_results:
            if block.table_row.cells[0][0].plain_text == cocktail_name:
                recipe = block.table_row.cells[1][0].plain_text
                ingredients = block.table_row.cells[2][0].plain_text
                break
        if recipe is None or ingredients is None:
            return JsonResponse({"message": "칵테일을 찾을 수 없습니다. 이름을 다시 확인해주세요."}, status=404)
    
    return JsonResponse({"recipe": recipe, "ingredients": ingredients, "cocktail_name": cocktail_name}, status=200)

@csrf_exempt
def update_stock(request):
    if request.method != "PATCH":
        return JsonResponse({"error": "PATCH only"}, status=405)

    block_id = os.getenv("STOCK_TABLE_ID")
    details = BlockDetail.model_validate_json(get_details(block_id).text)
    items = re.split(r'[,\n]+', json.loads(request.body).get("content").strip())
    items = [item.strip() for item in items if item.strip()]
    item_pairs = {}
    for item in items:
        key, value = item.split()
        item_pairs[key] = int(value)

    '''[수정 로직]
    1. body.content를 콤마(,)와 엔터(\n)로 절분.
    2. 
    '''

    url = f"{base_url}/blocks/{block_id}"
    payload = {
        "table_row": {
            # "cells": [
            #     [
            #         {
            #             "type": "text",
            #             "text": {
            #                 "content": update_content
            #             }
            #         }
            #     ],
            #     [
            #         {
            #             "type": "text",
            #             "text": {
            #                 "content": update_content
            #             }
            #         }
            #     ],
            #     [
            #         {
            #             "type": "text",
            #             "text": {
            #                 "content": update_content
            #             }
            #         }
            #     ]
            # ]
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

    return resp