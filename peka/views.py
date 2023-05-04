import json
from django.http import JsonResponse
from django.conf import settings

def data(request):
    with open("peka/data/main_heatmap.json") as f:
        data = json.load(f)
    for key, filename in [
        ["similarity", "similarity_score"], ["eRIC", "log2FC_eRIC"],
        ["recall", "recall"], ["introns", "3UTR%_intron%_5UTR+CDS%"],
        ["noncoding_IDR", "%_noncoding_IDR_peaks"],
        ["total_IDR", "total_IDR_peaks"], ["dendrogram", "dendrogram"]
    ]:
        with open(f"{settings.PEKA_ROOT}/{filename}.json") as f:
            data[key] = json.load(f)
    return JsonResponse(data)


def entities(request):
    with open(f"{settings.PEKA_ROOT}/main_heatmap.json") as f:
        data = json.load(f)
    return JsonResponse({
        "proteins": data["columns"], "motifs": data["rows"]
    })


def rbp(request):
    if name := request.GET.get("name"):
        try:
            with open(f"{settings.PEKA_ROOT}/rbp/{name}.json") as f:
                return JsonResponse(json.load(f))
        except FileNotFoundError:
            return JsonResponse({"error": "No such RBP"}, status=404)
    return JsonResponse({"error": "No RBP name given"}, status=400)


def motif(request):
    if not (sequence := request.GET.get("sequence")):
        return JsonResponse({"error": "No motif sequence given"}, status=400)
    with open(f"{settings.PEKA_ROOT}/motif/motif_groups.tsv") as f:
        groups = [l.split("\t") for l in f.read().splitlines()]
    for group in groups:
        if sequence in group[1].split(", "):
            with open(f"{settings.PEKA_ROOT}/motif/{group[0]}_full.json") as f:
                data = json.load(f)
                data["group"] = group[0]
                data["group_members"] = group[1].split(", ")
                return JsonResponse(data)
    return JsonResponse({"error": "No such motif"}, status=404)


def motif_lines(request):
    if sequence := request.GET.get("sequence"):
        try:
            with open(f"{settings.PEKA_ROOT}/motif/{sequence}_lineplot.json") as f:
                return JsonResponse(json.load(f))
        except FileNotFoundError:
            return JsonResponse({"error": "No such motif"}, status=404)
    return JsonResponse({"error": "No motif sequence given"}, status=400)