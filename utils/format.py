from datetime import datetime


def date_to_string(date):
    return date.strftime('%Y-%m-%d %H:%M:%S %Z')


def str_to_date(string):
    return datetime.strptime(string, '%Y-%m-%d %H:%M:%S %Z')
