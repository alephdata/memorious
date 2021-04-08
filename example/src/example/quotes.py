from urllib.parse import urljoin
import datafreeze


def login(context, data):
    # Get parameters from the stage which calls this method in the yaml file
    base_url = context.params.get("url")
    url = urljoin(base_url, "login")
    username = context.params.get("username")
    password = context.params.get("password")

    # Context wraps requests, and reuses the same session.
    # When we login here, this is persisted across future uses of
    # context.http
    res = context.http.get(url)
    # Get the login form and post the credentials.
    # Uses lxml under the hood.
    page = res.html
    form = page.find(".//form")
    login_url = urljoin(base_url, form.get("action"))
    login_data = {"username": username, "password": password}
    # We also need to pass the hidden inputs from the form.
    hidden_inputs = {
        h_in.get("name"): h_in.get("value")
        for h_in in form.xpath('./input[@type="hidden"]')
    }
    login_data.update(hidden_inputs)
    context.http.post(login_url, data=login_data)

    # Set data for input to the next stage, and proceed.
    # (The next stage is 'fetch' which takes a 'url' input.)
    data = {"url": base_url}
    context.emit(data=data)


def crawl(context, data):
    # This stage comes after 'fetch' so the 'data' input contains an
    # HTTPResponse object.
    response = context.http.rehash(data)
    url = response.url
    page = response.html

    # If we find a next link, recursively fetch that page by handing it back
    # to the 'fetch' stage.
    next_link = page.find('.//nav//li[@class="next"]/a')
    if next_link is not None:
        next_url = urljoin(url, next_link.get("href"))
        context.emit(rule="fetch", data={"url": next_url})

    # Parse the rest of the page to extract structured data.
    for quote in page.findall('.//div[@class="quote"]'):
        quote_data = {
            "text": quote.find('.//span[@class="text"]').text_content(),
            "author": quote.find('.//small[@class="author"]').text_content(),
            "tags": ", ".join(
                [tag.text_content() for tag in quote.findall('.//a[@class="tag"]')]
            ),  # noqa
        }

        # If 'rule' is not set, it defaults to 'pass', which triggers the
        # final 'store' stage.
        context.emit(data=quote_data)
    context.emit(rule="cleanup", data={"content_hash": response.content_hash})


def store(context, data):
    # This example uses a database to store structured data, which you can
    # access through context.datastore.
    table = context.datastore[context.params.get("table")]
    # The data is passed in from context.emit of the previous 'crawl' stage.
    table.upsert(data, ["text", "author"])


def export(context, params):
    table = context.datastore[params["table"]]
    datafreeze.freeze(table, format="json", filename=params["filename"])
