from urllib.parse import urljoin
from requests.exceptions import RequestException
from servicelayer.cache import make_key

from memorious.helpers.rule import Rule


def fetch(context, data):
    """Do an HTTP GET on the ``url`` specified in the inbound data."""
    url = data.get('url')
    attempt = data.pop('retry_attempt', 1)
    try:
        result = context.http.get(url, lazy=True)
        rules = context.get('rules', {'match_all': {}})
        if not Rule.get_rule(rules).apply(result):
            context.log.info('Fetch skip: %r', result.url)
            return

        if not result.ok:
            err = (result.url, result.status_code)
            context.emit_warning("Fetch fail [%s]: HTTP %s" % err)
            if not context.params.get('emit_errors', False):
                return
        else:
            context.log.info("Fetched [%s]: %r",
                             result.status_code,
                             result.url)

        data.update(result.serialize())
        if url != result.url:
            tag = make_key(context.run_id, url)
            context.set_tag(tag, None)
        context.emit(data=data)
    except RequestException as ce:
        retries = int(context.get('retry', 3))
        if retries >= attempt:
            context.log.warn("Retry: %s (error: %s)", url, ce)
            data['retry_attempt'] = attempt + 1
            context.recurse(data=data, delay=2 ** attempt)
        else:
            context.emit_warning("Fetch fail [%s]: %s" % (url, ce))


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

        rurl = urljoin(url, href)
        rdata = data.copy()
        rdata['url'] = rurl
        rdata['foreign_id'] = rurl
        if rdata['url'] == url:
            continue

        if resp.find('.//{DAV:}collection') is not None:
            rdata['parent_foreign_id'] = rurl
            context.log.info("Fetching contents of folder: %s" % rurl)
            context.recurse(data=rdata)
        else:
            rdata['parent_foreign_id'] = url

        # Do GET requests on the urls
        fetch(context, rdata)


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

    referer = context.get('url')
    if referer is not None:
        context.http.session.headers['Referer'] = referer

    proxy = context.get('proxy')
    if proxy is not None:
        proxies = {'http': proxy, 'https': proxy}
        context.http.session.proxies = proxies

    # Explictly save the session because no actual HTTP requests were made.
    context.http.save()
    context.emit(data=data)
