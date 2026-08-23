from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Split a string by the given delimiter"""
    return value.split(arg)
