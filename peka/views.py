import json
from django.http import JsonResponse

def data(request):
    with open("peka/data/main_heatmap.json") as f:
        data = json.load(f)
    for key, filename in [
        ["similarity", "similarity_score"], ["iBAQ", "iBAQ"],
        ["recall", "recall"], ["introns", "3UTR%_intron%_5UTR+CDS%"],
        ["noncoding_IDR", "%_noncoding_IDR_peaks"],
        ["total_IDR", "total_IDR_peaks"]
    ]:
        with open(f"peka/data/{filename}.json") as f:
            data[key] = json.load(f)
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