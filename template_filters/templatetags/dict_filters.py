from django import template

register = template.Library()

@register.filter
def dict_get(h, key):
    return h.get(key)
