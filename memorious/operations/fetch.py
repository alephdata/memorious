from urlparse import urljoin

from memorious.helpers.rule import Rule


def fetch(context, data):
    """Do an HTTP GET on the ``url`` specified in the inbound data."""
    url = data.get('url')
    result = context.http.get(url)

    rules = context.params.get('rules', {'match_all': {}})
    if not Rule.get_rule(rules).apply(result):
        context.log.info('Fetch skip: %r', result.url)
        return

    if not result.ok:
        context.log.warning("Fetch fail [%s]: %s",
                            result.status_code,
                            result.url)
        return

    context.log.info("Fetched [%s]: %r", result.status_code, result.url)
    data.update(result.serialize())
    if url != result.url:
        context.set_run_tag(result.url, None)
    context.emit(data=data)


def davindex(context, data):
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
