import json
from django.http import JsonResponse

def data(request):
    with open("peka/data.json") as f:
        data = json.load(f)
    return JsonResponse(data, safe=False)