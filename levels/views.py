from django.shortcuts import render
import json
# Create your views here.


def load_json_file(level):
    results = {}

    with open('common/asvs.json') as f:
        data = json.load(f)
    for r in data['requirements']:   
        bob = 'level{0}'.format(level)
        if r.get(bob):
            results.setdefault(r['section_name'], []).append(r)
    return results


def levels(request, level):
    results = load_json_file(level)
    return render(request, 'levels/levels.html', {'results': results, 'level': int(level)})
