# Building a crawler

Memorious contains all of the functionality for basic Web crawlers, which can be configured and customised entirely through YAML files. For more complex crawlers, Memorious can be extended with custom Python functions, which you can point a crawler at through its YAML config.

We'll start by describing the included functionality.

The first few lines of your config are to set up your crawler:

* `name`: A unique slug, eg. "my_crawler", which you can pass to `memorious run` to start your crawler.
* `description`: An optional description, will be shown when you run `list`.
* `schedule`: one of `daily`, `weekly` or `monthly`

## The Pipeline

Memorious crawlers are made up of stages, each of which take care of a particular part of a crawler's pipeline. Each stage takes an input from the previous stage, and yields an output for the next stage. For example, a crawling stage might find every URL on a webpage and pass it to a parsing stage which fetches and downloads the contents of each URL.

The first stage can be configured to automatically generate the starting input, or you can pass an input directly. [See initializers](#initializers).

The final stage is likely to be for storage, either via an API like [aleph](https://github.com/alephdata/aleph) or writing to disc. [See storing](#storing).

Every stage has access to the crawler's persistent [context](#context) object and the data that was passed from the previous stage. The `data` dict depends on the output of the previous stage. See the specific stages for what this looks like in each case.

You probably only need to think about the `context` if you're writing [extensions](#extending). 

## Stages

Each stage of a crawler is delimited by a child of the `pipeline` key in its YAML config. You can name the stages anything you like, and use these keys to refer to one stage from another.

A stage must contain:

* `method`: what do you want Memorious to do when it gets to this stage.
* `handle`: which stage is triggered next and under what conditions.
  * The default condition is `pass`. (ie. `pass: crawl` means in the case of a 'pass' condition invoke the stage called 'crawl').
  * Some in-built methods may return different conditions depending on the input - see method-specific sections. 
  * You will care more about this if you're [extending](#extending) Memorious.

```
name: my_crawler
pipeline:
  init:
    method: xxx
    ...
    handle: 
      pass: crawl
  crawl:
    method: yyy
    ...
    handle: 
      pass: save
  save:
    method: zzz
    ...
    
```

A stage may also contain a `params` key which lets you pass values *in* from the config. The data that comes *out* of each stage are available to the next stage via the `data` dict. Read on for the standard methods Memorious makes available to you, the parameters they take, and their output variables.

Skip to [extending](#extending) to see how to use custom methods if you need something that Memorious doesn't do.