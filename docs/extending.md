## Extending

If none of the inbuilt methods do it for you, you can write your own. You'll need to package your methods up into a python module, and install it (see installation instructions in readme). 

You can then call these methods from a YAML config instead of the Memorious ones. eg:

```
  my_stage:
    method: custom.module:my_method
    params:
      my_param: my_value
    handle:
      pass: store
```

Your method needs to accept two arguments, `context` and `data`.

The `data` dict is what was output from the previous stage, and what it contains depends on the the method from that stage. The [context object](#context) gives you access to various useful variables and helper functions...

### Context

From the YAML config:

* You can access `params` with `context.params.get('my_param')`.
* You can also access other properties of the crawler, eg. `context.get('name')` and `context.get('description')`.

The HTTP session:

* `context.http` is a wrapper for [requests](http://docs.python-requests.org/en/master/). Use `context.http.get` (or `.post`) just like you would use requests, and benefit from Memorious database caching; session persistence; lazy evaluation; and serialization of responses between crawler operations.
* Properties of the `ContextHTTPResponse` object:
 * `url`
 * `status_code`
 * `headers`
 * `encoding`
 * `file_path`
 * `content_hash`
 * `content_type`
 * `ok` (bool)
 * The content as `raw`, `text`, `html`, `xml`, or `json`

The datastore:

* Create and access tables in the Memorious database to store intermediary useful crawler data: `table = context.datastore['my_table']`.
* See [dataset](https://dataset.readthedocs.io/en/latest/) for the rest of how this works..

Output:

* To pass data from `my_method` to the next stage, use: `context.emit(data={'my_key': 'my_value'})`

### Helpers

Memorious contains useful helper functions you might like to use:

* TODO.