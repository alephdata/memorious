### Initializers

The initializer methods are:

* `sequence`: generate a sequence of numbers.
* `dates`: generate a sequence of dates.
* `enumerate`: loop through a list of items.
* `seed`: loop through a list of URLs.

#### Sequence

Parameters (all optional):

* `start`: the start of the sequence. Defaults to 1.
* `stop`: the end of the sequence.
* `step`: how much to increment by. Defaults to 1; can be negative.
* `delay`: numbers can be generated one by one with a delay to avoid large sequences clogging up the queue.
* `prefix`: a string which ensures each number will be emitted only once across multiple runs of the crawler.

If this stage is preceded by a stage which outputs a `number` (for example, another `sequence` stage), it will use this value as the start of the sequence instead of `start`.

Output data:

* `number`: the number in the sequence.

#### Dates

This generates a sequence of dates, counting backwards from `end`, either to `begin` or according to the number of `steps`, and the `days`/`weeks` value is the size of each step.

Parameters (all optional):

* `format`: date format to expect and/or output. Defaults to "%Y-%m-%d".
* `end`: latest date to generate (should match `format`). Defaults to 'now'.
* `begin`: earliest date to generate (should match `format`). Overrides `steps`.
* `days`: the time difference to increment by. Defaults to 0.
* `weeks`: the time difference to increment by. Defaults to 0.
* `steps`: The number of times to increment. Defaults to 100. Ignored if `begin` is set.

Output data:

* `date`: a date formatted by the input `format`.
* `date_iso`: a date in ISO format.

#### Enumerate

Emits each item in a list so they can be passed one at a time to the next stage.

Parameters:

* `items`: a list of items to loop through.

Output data:

* `item`: one of the items from the input list.

#### Seed

Starts a crawler with URLs, given as a list or single value .If this is called as a second stage in a crawler, the URL will be formatted against the supplied `data` values, ie: `https://crawl.site/entries/%(number)s.html`

Parameters:

* `url` or `urls`: one or more URLs to loop through.

Output data:

* `url`: each URL, with data from the previous stage substituted if applicable.

