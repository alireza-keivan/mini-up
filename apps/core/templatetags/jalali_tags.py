# apps/core/templatetags/jalali_tags.py

from django import template
import jdatetime

register = template.Library()


@register.filter(name='jalali')
def jalali_date(value, format_string='%Y/%m/%d - %H:%M'):
    """
    Convert Gregorian datetime to Jalali (Persian) date
    Usage: {{ some_date|jalali }}
    Custom format: {{ some_date|jalali:"%Y/%m/%d" }}
    """
    if not value:
        return ''
    
    try:
        if isinstance(value, str):
            return value
        
        # Convert to Jalali
        jalali_dt = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_dt.strftime(format_string)
    except Exception:
        return str(value)


@register.filter(name='jalali_short')
def jalali_date_short(value):
    """
    Convert to short Jalali date format (Y/m/d)
    Usage: {{ some_date|jalali_short }}
    """
    return jalali_date(value, '%Y/%m/%d')


@register.filter(name='jalali_full')
def jalali_date_full(value):
    """
    Convert to full Jalali datetime format
    Usage: {{ some_date|jalali_full }}
    """
    return jalali_date(value, '%Y/%m/%d - %H:%M:%S')
