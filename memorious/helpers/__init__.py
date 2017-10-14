from itertools import count
from stringcase import titlecase
from normality import slugify

from memorious.helpers.asp import ViewForm  # noqa


def convert_snakecase(name):
    name = titlecase(name)
    return slugify(name, sep='_')


def soviet_checksum(code):
    """Courtesy of Sir Vlad Lavrov."""
    def sum_digits(code, offset=1):
        total = 0
        for digit, index in zip(code[:7], count(offset)):
            total += int(digit) * index
        summed = (total / 11 * 11)
        return total - summed

    check = sum_digits(code, 1)
    if check == 10:
        check = sum_digits(code, 3)
        if check == 10:
            return code + '0'
    return code + str(check)
