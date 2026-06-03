from django.shortcuts import render

def handler404(request, *args, **argv):
    response = render(request,'404.html')
    response.status_code = 404
    return response

def handler500(request, *args, **argv):
    response = render(request,'500.html')
    response.status_code = 500
    return response
