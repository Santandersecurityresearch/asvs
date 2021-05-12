
from django.views.defaults import page_not_found
from django.shortcuts import render
from django.template import RequestContext

def handler404(request, *args, **argv):
    response = render(None,'404.html',
                              context_instance=RequestContext(request))
    response.status_code = 404
    return response

def handler500(request, *args, **argv):
    response = render(None,'500.html',
                              context_instance=RequestContext(request))
    response.status_code = 500
    return response