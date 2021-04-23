import json
from django.http import JsonResponse

def data(request):
    with open("peka/data/main_heatmap.json") as f:
        data = json.load(f)
    for key, filename in [
        ["similarity", "similarity_score"], ["eRIC", "log2FC_eRIC"],
        ["recall", "recall"], ["introns", "3UTR%_intron%_5UTR+CDS%"],
        ["noncoding_IDR", "%_noncoding_IDR_peaks"],
        ["total_IDR", "total_IDR_peaks"], ["dendrogram", "dendrogram"]
    ]:
        with open(f"peka/data/{filename}.json") as f:
            data[key] = json.load(f)
    return JsonResponse(data)


def entities(request):
    with open("peka/data/main_heatmap.json") as f:
        data = json.load(f)
    return JsonResponse({
        "proteins": data["columns"], "motifs": data["rows"]
    })


def rbp(request):
    name = request.GET.get("name")
    if name:
        try:
            with open(f"peka/data/rbp/{name}.json") as f:
                return JsonResponse(json.load(f))
        except FileNotFoundError:
            return JsonResponse({"error": "No such RBP"}, status=404)
    return JsonResponse({"error": "No RBP name given"}, status=400)


def motif(request):
    sequence = request.GET.get("sequence")
    if sequence:
        with open("peka/data/motif/motif_groups.tsv") as f:
            groups = [l.split("\t") for l in f.read().splitlines()]
        for group in groups:
            print(group)
            if sequence in group[1].split(", "):
                with open(f"peka/data/motif/{group[0]}_full.json") as f:
                    data = json.load(f)
                    data["group"] = group[0]
                    data["group_members"] = group[1].split(", ")
                    return JsonResponse(data)
        return JsonResponse({"error": "No such motif"}, status=404)
    return JsonResponse({"error": "No motif sequence given"}, status=400)