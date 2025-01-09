from django import template
from datetime import timedelta

register = template.Library()

@register.filter(name='break_location')
def break_location(value):
    words = value.split()
    if len(words) > 2:
        return ' '.join(words[:2]) + '<br>' + ' '.join(words[2:])
    return value

@register.filter
def add_days(value, days):
    try:
        days = int(days)
        return value + timedelta(days=days)
    except (ValueError, TypeError):
        return value