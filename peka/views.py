import json
from django.http import JsonResponse

def data(request):
    with open("peka/data/heatmap.json") as f:
        data = json.load(f)
    return JsonResponse(data)


def rbp(request):
    name = request.GET.get("name")
    if name:
        try:
            with open(f"peka/data/{name}.json") as f:
                return JsonResponse(json.load(f))
        except FileNotFoundError:
            return JsonResponse({"error": "No such RBP"}, status=404)
    return JsonResponse({"error": "No RBP name given"}, status=400)