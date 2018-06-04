from django.shortcuts import render
import json


def load_json_file(category):
    with open('common/category.json') as f:
        data = json.load(f)
    for d in data['categories']:
        if int(category) == d['id']:
            return d


def helping(request, category):
    data = load_json_file(category)
    return render(request, "help/help.html", {"data": data, 'category': data['title']})
