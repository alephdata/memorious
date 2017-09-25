from stringcase import titlecase
from normality import slugify


def convert_snakecase(name):
    name = titlecase(name)
    return slugify(name, sep='_')
