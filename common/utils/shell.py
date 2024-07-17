from datetime import date, datetime


def argparse_date(datestring):
    """
    Convert a string to a date object. Useful to use as argparse converter
    Args:
        datestring: the string to covert

    Returns: a datetime.date object

    """
    return datetime.strptime(str(datestring).strip()[:10], '%Y-%m-%d').date()