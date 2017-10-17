### Rules

You can configure rules per stage to tell certain methods which inputs to process or skip. You can nest them, and apply `not`,  `and` and `or` for the combinations you desire.

* `mime_type`: Match the MIME type string.
* `mime_group`: See [mime.py](https://github.com/alephdata/memorious/blob/master/memorious/helpers/mime.py) for handy MIME type groupings (`web`, `images`, `documents`, `archives` and `assets`).
* `domain`: URL contains this domain.
* `pattern`: URL matches this regex.
