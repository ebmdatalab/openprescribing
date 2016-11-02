import math

from django import template
from django.utils.safestring import mark_safe
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.simple_tag(takes_context=True)
def conditional_js(context, filename):
    tag_format = '<script src="/static/js/%s.%sjs?q=123456"></script>'
    if context.get('debug', False):
        tag = tag_format % (filename, '')
    else:
        tag = tag_format % (filename, 'min.')
    return mark_safe(tag)


@register.filter
def wholenum(num):
    return int(round(num))


@register.filter
def delta(num, arg):
    return abs(num - arg)


@register.filter
def roundpound(num):
    order = math.floor(math.log10(num))
    if order > 0:
        return intcomma(int(round(num/order) * order))
    else:
        return int(round(num))
