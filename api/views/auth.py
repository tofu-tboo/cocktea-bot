from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "username/password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "username already exists"}, status=400)

    user = User.objects.create_superuser(username=username, password=password) # 모두 관리자 권한 부여
    return JsonResponse({"message": "signup success", "id": user.id}, status=201)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"error": "invalid credentials"}, status=400)

    login(request, user)  # Django 세션 생성
    return JsonResponse({"message": "login success", "id": user.id})

@csrf_exempt
def logout(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    logout(request)  # 세션 제거
    return JsonResponse({"message": "logout success"})

@csrf_exempt
def delete_account(request):
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE only"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "not logged in"}, status=401)

    request.user.delete()
    logout(request)
    return JsonResponse({"message": "account deleted"})
