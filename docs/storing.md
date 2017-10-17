### Storing

The final stage of a crawler is to store the data you want.

#### Directory

The `directory` method stores the collected files in the given directory.

The input data from the previous stage is expected to be a `ContextHttpResponse` object.

Parameters:

* `path`: the directory to store files in, relative to the `MEMORIOUS_BASE_PATH` environment variable (another directory will be created in here, named after the specific crawler, so it's safe to pass the same `path` to multiple crawlers). 

Output:

* The file is stored in `path`.
* The `data` dict is dumped as a JSON file in `path` too.

#### Aleph

If you've configured the environment variables for `MEMORIOUS_ALEPH_HOST` and `MEMORIOUS_ALEPH_API_KEY`, you can store to any instance of the [Aleph](https://github.com/alephdata/aleph) v2.0+ API with the `aleph_emit` method.

The `data` from the previous stage is expected to include a `ContextHttpResponse` object, as well as:

* `title`: set by `documentcloud` or a prior `parse` stage.
* `author`: set by `documentcloud`
* `countries`: set by `documentcloud`
* `languages`: set by `documentcloud`
* `mime_type`: set by `documentcloud` (optional, defaults to MIME type from the HTTP response)
* `foreign_id`: set by `documentcloud` (optional, defaults to `request_id` from the HTTP response)
* `source_url`: set by `documentcloud` (optional, defaults to the URL of the HTTP request)

Parameters:

* `collection`: the slug for the Aleph collection documents should be stored in.
