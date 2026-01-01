from django import template

register = template.Library()


@register.filter(name='abs_value')
def abs_value(value):
    """Return the absolute value of a number"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value


@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
