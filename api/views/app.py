from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def status(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    return JsonResponse({"status": "ok"}, status=200)