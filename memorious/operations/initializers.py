from banal import ensure_list
from datetime import datetime, timedelta


def seed(context, data):
    """Initialize a crawler with a set of seed URLs.

    The URLs are given as a list or single value to the ``urls`` parameter.

    If this is called as a second stage in a crawler, the URL will be formatted
    against the supplied ``data`` values, e.g.:

        https://crawl.site/entries/%(number)s.html
    """
    for key in ('url', 'urls'):
        for url in ensure_list(context.params.get(key)):
            url = url % data
            context.emit(data={'url': url})


def enumerate(context, data):
    """Iterate through a set of items and emit each one of them."""
    items = ensure_list(context.params.get('items'))
    for item in items:
        data['item'] = item
        context.emit(data=data)


def sequence(context, data):
    """Generate a sequence of numbers.

    It is the memorious equivalent of the xrange function, accepting the
    ``start``, ``stop`` and ``step`` parameters.

    This can run in two ways:
    * As a single function generating all numbers in the given range.
    * Recursively, generating numbers one by one with an optional ``delay``.

    The latter mode is useful in order to generate very large sequences
    without completely clogging up the user queue.

    If an optional ``tag`` is given, each number will be emitted only once
    across multiple runs of the crawler.
    """
    number = data.get('number', context.params.get('start', 1))
    stop = context.params.get('stop')
    step = context.params.get('step', 1)
    delay = context.params.get('delay')
    prefix = context.params.get('tag')
    while True:
        tag = None if prefix is None else '%s:%s' % (prefix, number)

        if tag is None or not context.check_tag(tag):
            data['number'] = number
            context.emit(data=data)

        if tag is not None:
            context.set_tag(tag, True)

        number = number + step
        if step > 0 and number >= stop:
            break
        if step < 0 and number <= stop:
            break

        if delay is not None:
            data['number'] = number
            context.recurse(data=data, delay=delay)
            break


def dates(context, data):
    format = context.params.get('format', '%Y-%m-%d')
    delta = timedelta(days=context.params.get('days', 0),
                      weeks=context.params.get('weeks', 0))
    if delta == timedelta():
        context.log.error("No interval given: %r", context.params)
        return

    if 'end' in context.params:
        current = context.params.get('end')
        current = datetime.strptime(current, format)
    else:
        current = datetime.utcnow()

    if 'current' in data:
        current = datetime.strptime(data.get('current'), format)

    if 'begin' in context.params:
        begin = context.params.get('begin')
        begin = datetime.strptime(begin, format)
    else:
        steps = context.params.get('steps', 100)
        begin = current - (delta * steps)

    context.emit(data={
        'date': current.strftime(format),
        'date_iso': current.isoformat()
    })
    current = current - delta
    if current >= begin:
        data = {'current': current.strftime(format)}
        context.recurse(data=data)
