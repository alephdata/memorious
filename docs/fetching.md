### Fetching and parsing

#### Fetch

The `fetch` method does an HTTP `GET` on the value of `url` in data passed from the previous stage.

Parameters (optional):

* `rules`: only the URLs which match are retrieved. See [Rules](#rules).

Output data:

* TODO: the serialized result of the GET response

#### DAV index

The `dav_index` method lists the files in a WebDAV directory; the directory is passed via the `url` of the previous stage data.

Output data:

* TODO

#### Session

The `session` method sets some HTTP parameters for all subsequent requests.

Parameters:

* `user`: for HTTP Basic authentication.
* `password`: for HTTP Basic authentication.
* `user_agent`: the User-Agent HTTP header.

Output data: 

* Emits the same `data` dict that was passed in, unmodified.

#### Parse

The `parse` method recursively finds URLs in webpages. It looks in the `href` attributes of `a` and `link` elements, and the `src` attributes of `img` and `iframe` elements. 

As `data` input from the previous stage, it expects a `ContextHttpResponse` object.

Parameters (optional):

* `store`: only the results which match are stored. See [Rules](#rules). If no rules are passed, everything is stored.

Output:

* If the input data contains HTML, it passes each URL it finds therein to the current stage's `fetch` handler.
* The input data (unmodified) is also passed to the current stage's `store` handler, filtered by any [rules](#rules) passed via the `store` param if applicable.

An example `parse` configuration, which crawls links and stores only documents:

```
  parse:
    method: parse
    params:
      store:
        mime_group: documents
    handle:
      fetch: fetch
      store: store
```

#### DocumentCloud

The `documentcloud_query` method harvests documents from a documentcloud.org instance.

Parameters:

* `host`: the URL of the DocumentCloud host. Defaults to 'https://documentcloud.org/'.
* `instance`: the name of the DocumentCloud instance. Defaults to 'documentcloud'.
* `query`: the query to send to the DocumentCloud search API.

Output data:

* `url`: the URL of the document.
* `source_url`: the canonical URL from documentcloud metadata.
* `foreign_id`: a unique ID from the instance and the document ID.
* `file_name`: where the document is stored locally (?).
* `mime_type`: hardcoded to `application/pdf`.
* `title`: from documentcloud metadata.
* `author`: from documentcloud metadata.
* `languages`: from documentcloud metadata.
* `countries`: from documentcloud metadata.



