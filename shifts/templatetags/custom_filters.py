from django import template

register = template.Library()

@register.filter(name='break_location')
def break_location(value):
    words = value.split()
    if len(words) > 2:
        return ' '.join(words[:2]) + '<br>' + ' '.join(words[2:])
    return value