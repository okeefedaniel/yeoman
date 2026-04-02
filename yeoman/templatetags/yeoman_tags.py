from django import template

from yeoman.workflow import STATUS_DISPLAY

register = template.Library()


@register.inclusion_tag('yeoman/_status_badge.html')
def status_badge(status):
    display = STATUS_DISPLAY.get(status, {'label': status, 'bg': 'secondary'})
    return {'label': display['label'], 'bg': display['bg']}


@register.filter
def priority_class(priority):
    return {
        'urgent': 'danger',
        'high': 'warning text-dark',
        'normal': 'secondary',
        'low': 'light text-dark',
    }.get(priority, 'secondary')
