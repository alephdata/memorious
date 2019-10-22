=========
Memorious
=========

.. image:: https://github.com/alephdata/memorious/workflows/memorious/badge.svg

    The solitary and lucid spectator of a multiform, instantaneous and almost intolerably precise world.
    
    -- `Funes the Memorious <http://users.clas.ufl.edu/burt/spaceshotsairheads/borges-funes.pdf>`_,
    Jorge Luis Borges

``memorious`` is a distributed web scraping toolkit. It is a light-weight tool
that schedules, monitors and supports scrapers that collect structured or
un-structured data. This includes the following use cases:

* Maintain an overview of a fleet of crawlers
* Schedule crawler execution in regular intervals
* Store execution information and error messages
* Distribute scraping tasks across multiple machines
* Make crawlers modular and simple tasks re-usable
* Get out of your way as much as possible

.. image:: docs/memorious-ui.png

Design
------

When writing a scraper, you often need to paginate through through an index
page, then download an HTML page for each result and finally parse that page
and insert or update a record in a database.

``memorious`` handles this by managing a set of ``crawlers``, each of which 
can be composed of multiple ``stages``. Each ``stage`` is implemented using a
Python function, which can be re-used across different ``crawlers``.

The basic steps of writing a Memorious crawler:

1. Make YAML crawler configuration file
2. Add different stages
3. Write code for stage operations (optional)
4. Test, rinse, repeat

Documentation
-------------

The documentation for Memorious is available at
`memorious.readthedocs.io <https://memorious.readthedocs.io/>`_.
Feel free to edit the source files in the ``docs`` folder and send pull requests for improvements.

To build the documentation, inside the ``docs`` folder run ``make html``

You'll find the resulting HTML files in /docs/_build/html.
