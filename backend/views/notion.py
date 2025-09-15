import os, json, unicodedata, random, re, time
from enum import Enum
from urllib.parse import unquote
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .dto.notion_dto import BlockDetail, Block, TableRow, RichText, Text, Annotations
from .dto.table_dto import StockTableRow, Ingredient, RecipeTableRow
from .util.log import debug_log

headers = {
    "Authorization": f"Bearer {os.getenv("NOTION_SECRET")}",
    "Content-Type": "application/json",
    "Notion-Version": f"{os.getenv("NOTION_VERSION")}",
}
base_url = "https://api.notion.com/v1"



@csrf_exempt
def get_recipe(request, cocktail_name):
    try:
        if request.method != "GET":
            raise ApiError(ErrorCode.GET_ONLY)

        # 1. Get a Table
        block_id = os.getenv("RECIPE_TABLE_ID")
        details = get_details_dto(block_id)
        cocktail_name = unicodedata.normalize("NFC", unquote(cocktail_name))

        table_check(details)

        # 2. Set Params
        recipe = None
        ingredients = None
        column_label = get_column_label(details, "칵테일 이름", "레시피", "필요 재료")
        
        # 3. Filter Table Rows
        filtered_results = cut_label_row(details.results)
        filtered_results = remove_empty_rows(filtered_results)
        
        # 4. Find Recipe
        if cocktail_name in ["아무거나", "랜덤", "random", "뽑기"]:
            random.shuffle(filtered_results)
            recipe = filtered_results[0].table_row.cells[column_label["레시피"]][0].plain_text
            ingredients = filtered_results[0].table_row.cells[column_label["필요 재료"]][0].plain_text
            cocktail_name = filtered_results[0].table_row.cells[column_label["칵테일 이름"]][0].plain_text
        else:
            for block in filtered_results:
                if block.table_row.cells[column_label["칵테일 이름"]][0].plain_text == cocktail_name:
                    recipe = block.table_row.cells[column_label["레시피"]][0].plain_text
                    ingredients = block.table_row.cells[column_label["필요 재료"]][0].plain_text
                    break
            if recipe is None or ingredients is None:
                raise ApiError(ErrorCode.CANNOT_FIND_COCKTAIL)
        return JsonResponse({"recipe": recipe, "ingredients": ingredients, "cocktail_name": cocktail_name}, status=200)
    except ApiError as e:
        if type(e.error_code) is ErrorCode:
            return error_resp(e.error_code)
        return error_resp(ErrorCode.UNKNOWN)
@csrf_exempt
def update_stock(request):
    try:
        if request.method != "PATCH":
            raise ApiError(ErrorCode.PATCH_ONLY)

        # 1. Get a Table
        block_id = os.getenv("STOCK_TABLE_ID")
        details = get_details_dto(block_id)

        table_check(details)

        # 2. Set Params
        column_label = get_column_label(details, "품명", "잔여 용량", "개수", "대치어")
        name_map = {}
        substitutes = {}
        
        # 3. Filter Table Rows
        filtered_results = cut_label_row(details.results)
        filtered_results = remove_empty_rows(filtered_results)

        # 4. Resolve Substitutes
        for block in filtered_results:
            name = block.table_row.cells[column_label["품명"]][0].plain_text
            substitution = block.table_row.cells[column_label["대치어"]][0].plain_text
            substitution_list = substitution.split(',')

            name_map[name] = { "id": block.id, "remains": float(block.table_row.cells[column_label["잔여 용량"]][0].plain_text), "count": int(block.table_row.cells[column_label["개수"]][0].plain_text), "substitution": substitution }
            for sub in substitution_list:
                substitutes[sub.strip()] = name
        
        # 4. Parse Request Body
        usages = re.split(r'[,\n]+', json.loads(request.body).get("content").strip())
        usages = [usage.strip() for usage in usages if usage.strip()]
        usages_map = {}
        for usage in usages:
            key, value = usage.split()
            if key in substitutes:
                name = substitutes[key]
            elif key in name_map:
                name = key
            else:
                raise ApiError(ErrorCode.INVALID_NAMES)

            remains = value.split('+')
            if len(remains) > name_map[name]["count"]:
                raise ApiError(ErrorCode.INVALID_AMOUNTS)
            for i in range(len(remains)):
                remains[i] = float(remains[i])
            usages_map[name] = remains

        '''[수정 로직]
        1. body.content를 콤마(,)와 엔터(\n)로 절분.
        2. dict로 포장.
        3. 테이블의 대치어와 비교하여 실제 품명으로 치환.
        4. 업데이트 내용이 기존 내용보다 작으면 업데이트 수행.
        5. 업데이트 내용이 0이면 개수 -1.
        '''

        harsh_stocks = []
        for name, data in usages_map.items():
            max_usage = max(data)
            min_usage = min(data)
            url = f"{base_url}/blocks/{name_map[name]["id"]}"
            update_content = [{}, {}, {}, {}]

            new_remain = max_usage
            new_count = name_map[name]["count"] if min_usage > 0 else name_map[name]["count"] - len([datum for datum in data if datum == 0])
            if new_count == 0 or (new_count == 1 and new_remain <= 5):
                harsh_stocks.append(name)

            update_content[column_label["품명"]] = {
                "type": "text",
                "text": {
                    "content": name
                }
            }
            update_content[column_label["잔여 용량"]] = {
                "type": "text",
                "text": {
                    "content": str(new_remain)
                }
            }
            update_content[column_label["개수"]] = {
                "type": "text",
                "text": {
                    "content": str(new_count)
                }
            }
            update_content[column_label["대치어"]] = {
                "type": "text",
                "text": {
                    "content": name_map[name]["substitution"]
                }
            }
            payload = {
                "table_row": {
                    "cells": [
                        [
                            update_content[0]
                        ],
                        [
                            update_content[1]
                        ],
                        [
                            update_content[2]
                        ],
                        [
                            update_content[3]
                        ]
                    ]
                }
            }

            request_with_retry(url, "PATCH", headers=headers, payload=payload)
        res_json = {
            "message": "업데이트 완료."
        }
        if len(harsh_stocks) > 0:
            res_json["admin_message"] = "다음 품목의 재고가 부족합니다: " + ", ".join(harsh_stocks)
        return JsonResponse(res_json, status=200)
    except ApiError as e:
        if type(e.error_code) is ErrorCode:
            return error_resp(e.error_code)
        return error_resp(ErrorCode.UNKNOWN)


def get_details(block_id):
    resp = request_with_retry(f"{base_url}/blocks/{block_id}/children", "GET", headers=headers)
    if type(resp) is BaseException:
        raise resp
    return resp

def get_details_dto(block_id):
    resp = get_details(block_id)
    return BlockDetail.model_validate_json(resp.text)

def table_check(details):

    if details.object != "list":
        raise ApiError(ErrorCode.NOT_A_LIST)
    elif len(details.results) == 0:
        raise ApiError(ErrorCode.EMPTY_LIST)
    
def get_column_label(table, *args):
    column_map = {}
    label_row = table.results[0].table_row.cells
    for arg in args:
        found = False
        for i in range(len(label_row)):
            if i in column_map.values():
                continue
            elif arg in label_row[i][0].plain_text: # 일치하는 구간이 있으면 라벨로 치부
                column_map[arg] = i
                found = True
                break
        if not found:
            raise ApiError(ErrorCode.INVALID_LABELS)
    return column_map

def cut_label_row(table):
    filtered = [block for block in table if block.type == "table_row" and block.table_row is not None]
    if len(filtered) == 0:
        raise ApiError(ErrorCode.NO_TABLE_ROWS)
    filtered.pop(0) # 첫번째 행은 헤더이므로 제거
    return filtered

def remove_empty_rows(table):
    filtered = [block for block in table if block.type == "table_row" and block.table_row is not None]
    if len(filtered) == 0:
        raise ApiError(ErrorCode.NO_TABLE_ROWS)
    non_empty = []
    for block in filtered:
        is_empty = True
        for cell in block.table_row.cells:
            if cell and len(cell) > 0 and cell[0].plain_text.strip() != "":
                is_empty = False
                break
        if not is_empty:
            non_empty.append(block)
    return non_empty

class ErrorCode(Enum):
    INVALID_LABELS = "Invalid Labels"
    NO_TABLE_ROWS = "No Table Rows"
    NOT_A_LIST = "Not a List"
    EMPTY_LIST = "Empty List"
    GET_ONLY = "GET Only"
    PATCH_ONLY = "PATCH Only"
    CANNOT_FIND_COCKTAIL = "Cannot Find Cocktail"
    UNKNOWN = "Unknown Error"
    NOTION_ERROR = "Notion API Error"
    NETWORK_ERROR = "Network Error"
    INVALID_NAMES = "Invalid Names"
    INVALID_AMOUNTS = "Invalid Amounts"
class ApiError(Exception):
    def __init__(self, error_code: ErrorCode):
        self.error_code = error_code
def error_resp(type: ErrorCode):
    match type:
        case ErrorCode.INVALID_LABELS:
            debug_log("❌ Invalid Labels")
            return JsonResponse({"message": "관리자에게 문의하세요. (Invalid Labels)"}, status=500)
        case ErrorCode.NO_TABLE_ROWS:
            debug_log("❌ No Table Rows")
            return JsonResponse({"message": "관리자에게 문의하세요. (No Table Rows)"}, status=500)
        case ErrorCode.NOT_A_LIST:
            debug_log("❌ Not a List")
            return JsonResponse({"message": "관리자에게 문의하세요. (Not a List)"}, status=500)
        case ErrorCode.EMPTY_LIST:
            debug_log("❌ Empty List")
            return JsonResponse({"message": "관리자에게 문의하세요. (Empty List)"}, status=500)
        case ErrorCode.GET_ONLY:
            return JsonResponse({"message": "관리자에게 문의하세요. (GET Only"}, status=405)
        case ErrorCode.PATCH_ONLY:
            return JsonResponse({"message": "관리자에게 문의하세요. (PATCH Only)"}, status=405)
        case ErrorCode.CANNOT_FIND_COCKTAIL:
            debug_log("❌ Cannot Find Cocktail")
            return JsonResponse({"message": "칵테일을 찾을 수 없습니다. 명령어를 다시 확인해주세요."}, status=404)
        case ErrorCode.UNKNOWN:
            debug_log("❌ Unknown Error")
            return JsonResponse({"message": "관리자에게 문의하세요. (Unknown Error)"}, status=500)
        case ErrorCode.NOTION_ERROR:
            debug_log("❌ Notion API Error")
            return JsonResponse({"message": "관리자에게 문의하세요. (Notion API Error)"}, status=500)
        case ErrorCode.NETWORK_ERROR:
            debug_log("❌ Network Error")
            return JsonResponse({"message": "관리자에게 문의하세요. (Network Error)"}, status=500)
        case ErrorCode.INVALID_NAMES:
            debug_log("❌ Invalid Names")
            return JsonResponse({"message": "품명이 올바르지 않습니다. 명령어를 다시 확인해주세요."}, status=404)
        case ErrorCode.INVALID_AMOUNTS:
            debug_log("❌ Invalid Amounts")
            return JsonResponse({"message": "잔여 용량이 올바르지 않습니다. 명령어를 다시 확인해주세요."}, status=400)
    return None

def request_with_retry(url, method, headers=None, payload=None, max_retries=8, timeout=10):
    for _ in range(max_retries):  # Retry up to max_retries times
        try:
            resp = requests.request(method, url, headers=headers, timeout=timeout, json=payload)
            resp.raise_for_status()
            debug_log("✅ Success!")
            # debug_log(json.dumps(resp.json(), indent=2, ensure_ascii=False))
            return resp
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = int(e.response.headers.get("Retry-After", 1))
                print("***********")
                debug_log(f"⚠️ Rate limited. Retrying after {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                debug_log("❌ HTTP error:", e.response.status_code, e.response.text)
            raise ApiError(ErrorCode.NOTION_ERROR)
        except requests.exceptions.RequestException as e:
            debug_log("❌ Request failed:", e)
            raise ApiError(ErrorCode.NETWORK_ERROR)

    debug_log("❌ Max retries exceeded.")
    raise ApiError(ErrorCode.NOTION_ERROR)