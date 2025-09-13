from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def status(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    return JsonResponse({"status": "ok"}, status=200)