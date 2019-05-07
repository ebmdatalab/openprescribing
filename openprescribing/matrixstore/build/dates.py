DEFAULT_NUM_MONTHS = 60


def generate_dates(end_str, months=None):
    """
    Given an end date as a string in YYYY-MM form (or the underscore separated
    equivalent), return a list of N consecutive months as strings in YYYY-MM-01
    form, with that month as the final member
    """
    if months is None:
        months = DEFAULT_NUM_MONTHS
    end_date = parse_date(end_str)
    assert months > 0
    dates = []
    for offset in range(1-months, 1):
        date = increment_months(end_date, offset)
        dates.append('{:04d}-{:02d}-01'.format(date[0], date[1]))
    return dates


def parse_date(date_str):
    """
    Given a date string in YYYY-MM form (or the underscore separated
    equivalent), return a pair of (year, month) integers
    """
    year_str, month_str = date_str.replace('_', '-').split('-')[:2]
    assert len(year_str) == 4
    assert len(month_str) == 2
    return int(year_str), int(month_str)


def increment_months((year, month), months):
    """
    Given a pair of (year, month) integers return the (year, month) pair N
    months in the future
    """
    i = (year*12) + (month - 1)
    i += months
    return int(i/12), (i % 12) + 1
