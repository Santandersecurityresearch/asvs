from django.shortcuts import render
import json
# Create your views here.


def load_json_file(level):
    results = []
    with open('common/asvs.json') as f:
        data = json.load(f)
    # if level == 0:
    #     for r in data['requirements']:
    #         if results.get(r['sectionTitle']):
    #             results[r['sectionTitle']].append(r['title'])
    #         else:
    #             results[r['sectionTitle']] = [r['title']]
    # else:
    for r in data['requirements']:
        bob = 'L{0}'.format(level)
        if r.get(bob):
            results.append(r)
            # if results.get(r['sectionTitle']):
            #     results[r['sectionTitle']].append(r['title'])
            # else:
            #     results[r['sectionTitle']] = [r['title']]
    return results


def levels(request, level):
    data = load_json_file(level)
    return render(request, 'levels/levels.html', {'data': data, 'level': int(level)})
