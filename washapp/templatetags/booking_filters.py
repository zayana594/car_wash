from django import template

register = template.Library()

@register.filter
def filter_by_status(bookings, statuses):
    status_list = [s.strip() for s in statuses.split(",")]
    return bookings.filter(status__in=status_list)
