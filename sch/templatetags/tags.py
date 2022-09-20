from django import template

register = template.Library()





@register.simple_tag
def secToHours(seconds):
    return seconds.total_seconds() / 3600