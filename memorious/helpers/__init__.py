from itertools import count
from stringcase import titlecase
from normality import slugify

from memorious.helpers.asp import ViewForm  # noqa
from memorious.helpers.dates import parse_date  # noqa
from memorious.helpers.key import make_id  # noqa


def convert_snakecase(name):
    if name.upper() != name:
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


def search_results_total(html, xpath, check, delimiter):
    """ Get the total number of results from the DOM of a search index. """
    for container in html.findall(xpath):
        if check in container.findtext('.'):
            text = container.findtext('.').split(delimiter)
            total = int(text[-1].strip())
            return total


def search_results_last_url(html, xpath, label):
    """ Get the URL of the 'last' button in a search results listing. """
    for container in html.findall(xpath):
        if container.text_content().strip() == label:
            return container.find('.//a').get('href')
