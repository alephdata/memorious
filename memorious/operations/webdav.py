from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote


def _get_url_file_name(url):
    path = urlparse(url).path
    try:
        path = unquote(path)
    except (TypeError, ValueError):
        pass
    return Path(path).name


def dav_index(context, data):
    """List files in a WebDAV directory."""
    # This is made to work with ownCloud/nextCloud, but some rumor has
    # it they are "standards compliant" and it should thus work for
    # other DAV servers.
    url = data.get("url")
    context.log.info("Fetching WebDAV path: %s" % url)
    result = context.http.request("PROPFIND", url)
    for resp in result.xml.findall("./{DAV:}response"):
        href = resp.findtext("./{DAV:}href")
        if href is None:
            continue

        child_url = urljoin(url, href)
        if child_url == url:
            continue
        child = dict(data)
        child["url"] = child_url
        child["foreign_id"] = child_url
        child["file_name"] = _get_url_file_name(href)

        rule = "file"
        if resp.find(".//{DAV:}collection") is not None:
            rule = "folder"
        context.emit(data=child, rule=rule)
