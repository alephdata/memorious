from urlparse import urljoin

from memorious.helpers.rule import Rule
from memorious.util import make_key


def fetch(context, data):
    """Do an HTTP GET on the ``url`` specified in the inbound data."""
    url = data.get('url')
    result = context.http.get(url)

    rules = context.get('rules', {'match_all': {}})
    if not Rule.get_rule(rules).apply(result):
        context.log.info('Fetch skip: %r', result.url)
        return

    if not result.ok:
        context.emit_warning("Fetch fail [%s]: %s",
                             result.status_code,
                             result.url)
        return

    context.log.info("Fetched [%s]: %r", result.status_code, result.url)
    data.update(result.serialize())
    if url != result.url:
        tag = make_key((context.run_id, url))
        context.set_tag(tag, None)
    context.emit(data=data)


def dav_index(context, data):
    """List files in a WebDAV directory."""
    # This is made to work with ownCloud/nextCloud, but some rumor has
    # it they are "standards compliant" and it should thus work for
    # other DAV servers.
    url = data.get('url')
    result = context.http.request('PROPFIND', url)
    for resp in result.xml.findall('./{DAV:}response'):
        href = resp.findtext('./{DAV:}href')
        if href is None:
            continue

        rdata = data.copy()
        rdata['url'] = urljoin(url, href)
        if rdata['url'] == url:
            continue

        if resp.find('.//{DAV:}collection') is not None:
            context.recurse(data=rdata)
        else:
            context.emit(data=rdata)


def session(context, data):
    """Set some HTTP parameters for all subsequent requests.

    This includes ``user`` and ``password`` for HTTP basic authentication,
    and ``user_agent`` as a header.
    """
    context.http.reset()

    user = context.get('user')
    password = context.get('password')
    if user is not None and password is not None:
        context.http.session.auth = (user, password)

    user_agent = context.get('user_agent')
    if user_agent is not None:
        context.http.session.headers['User-Agent'] = user_agent

    context.emit(data=data)
