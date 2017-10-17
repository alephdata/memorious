## Usage

``memorious`` is controlled via a command-line tool, which can be used to monitor
or invoke a crawler interactively. Most of the actual work, however, is handled
by a daemon service running in the background. Communication between different
components is handled via a central message queue.

See the status of all crawlers managed by memorious:

```sh
memorious list
```

Force an immediate run of a specific crawler:

```sh
memorious run my_crawler
```

Check which crawlers are due for scheduled execution and execute the ones that
need to be updated:

```sh
memorious scheduled
```

Clear all the run status and cached information associated with a crawler:

```sh
memorious flush my_crawler
```

