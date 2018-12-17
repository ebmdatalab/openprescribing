import math

from django import template
from django.utils.safestring import mark_safe
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone


register = template.Library()


try:
    from django.utils.html import json_script
except ImportError:
    from ._json_script_backport import json_script
    register.filter('json_script', json_script, is_safe=True)
else:
    raise RuntimeError(
        'Please remove the `_json_script_backport` module now that we are '
        'using a version of Django which provides the `json_script` '
        'template tag by default')


@register.simple_tag(takes_context=True)
def conditional_js(context, filename):
    tag_format = '<script src="/static/js/%s.%sjs"></script>'
    if context.get('DEBUG', True):
        tag = tag_format % (filename, '')
    else:
        tag = tag_format % (filename, 'min.')
    return mark_safe(tag)


@register.filter
def wholenum(num):
    return int(round(num))


@register.filter
def deltawords(num, arg):
    """An adverb to come after the word 'improved' or 'slipped'
    """
    delta = abs(num - arg)
    # We only pick out changes over 10%; over 30% in 9 months is unheard of.
    if delta == 0:
        word = "not at all"
    elif delta < 10:
        word = "slightly"
    elif delta < 20:
        word = "moderately"
    elif delta < 30:
        word = "considerably"
    else:
        word = "massively"
    return word


@register.filter
def roundpound(num):
    order = 10 ** math.floor(math.log10(num))
    if order > 0:
        return intcomma(int(round(num/order) * order))
    else:
        return str(int(round(num)))


@register.filter
def sigfigs(value, figures=3):
    """
    Round value to supplied significant figures
    """
    if not value:
        value = 0
    order = int(math.floor(math.log10(math.fabs(value))))
    places = figures - order - 1
    format_string = '{:.%df}' % max(0, places)
    return format_string.format(round(value, places))


@register.simple_tag
def url_toggle(request, field):
    dict_ = request.GET.copy()
    if field in dict_:
        del(dict_[field])
    else:
        dict_[field] = 1
    return dict_.urlencode()


@register.simple_tag
def current_time(format_string):
    return timezone.now().strftime(format_string)


@register.filter
def fancy_join(lst, sep=', ', final_sep=' and '):
    """
    Join a list using a different separator for the final element
    """
    if len(lst) > 2:
        head, tail = lst[:-1], lst[-1]
        lst = [sep.join(head), tail]
    return final_sep.join(lst)
