## elogs

elogs is a Python module and a REST service to access static, local
[elog](https://midas.psi.ch/elog/) logbooks.

## API

The API is split into different layers. The lowest layer contains the `Logbook`
and `Entry` classes representing a single elog logbook and its entries. To load
the `demo` logbook and list all its `entries` (a dict mapping ID to entry) you
have to provide a path like

```python
import elogs

log = elogs.Logbook('/path/to/logbooks/demo')

for entry in log.entries.values():
    print(entry)
```

The `Entry` class provides an `attributes` dict, an integer `id` , a
`datetime` `date` and a string `comment`. To enumerate *all* logbooks you can
use the `Storage` class and pass the root path:

```python
storage = log.Storage('/path/to/logbooks')
print(storage.logbooks.keys())
```

On top of the basic layer, there is a `query` API to filter among attributes and
date fields. Complex queries can be constructed by combining simple expressions
and conjunctions. For example to get all the logs of John and Jane Doe you would
write:

```python
from elogs.query import query, And, Eq

results = query(log, And(Eq('Name', 'John Doe'), Eq('Name', 'Jane Doe')))
print(results)
```

By matching the `date` field we can also retrieve all entries that happened
between 3 and 6pm, August 23rd 2017:

```python
from dateutil.parser import parse
from elogs.query import query, And, Before, After

results = query(log,
    And(
      After(parse('23 Aug 2017 15:00 +0200')),
      Before(parse('23 Aug 2017 18:00 +0200'))
    ))
```


## REST service

The `elogsd` script is a small Flask server that reads logbooks and provides a
REST interface to query and filter the logbook data. To run it, you have to set
the environment variable `ELOGSD_PATH` to the location containing the logbooks:

    ELOGSD_PATH=/var/lib/elog/logbooks ./elogsd

On success you can ask for the available logbooks on the root endpoint and get a
JSON array with the logbook names:

    > curl http://127.0.0.1:5000
    < [
        "foo",
        "bar"
      ]

Querying for a logbook retrieves all logbook entries:

    > curl http://127.0.0.1:5000/foo
    < [
        {
          "attributes": {
            "$@MID@$": "2",
            "Attachment": "",
            "Name": "foo",
            "Date": "Wed, 02 Sep 2015 12:53:38 +0200",
          },
          "date": "Wed, 02 Sep 2015 12:53:38 GMT",
          "id": 2
        },
        {
          "attributes": {
            "$@MID@$": "3",
            "Attachment": "",
            "Name": "bar",
            "Date": "Wed, 02 Sep 2015 12:58:06 +0200",
          },
          "date": "Wed, 02 Sep 2015 12:58:06 GMT",
          "id": 3
        }
      ]

The resulting set can be reduced by adding an escaped query string. For example
to find all entries with `Name` `bar` you would query:

    > curl http://127.0.0.1:5000/foo?q="a:Name=bar"
    <
        {
          "attributes": {
            "$@MID@$": "3",
            "Attachment": "",
            "Name": "bar",
            "Date": "Wed, 02 Sep 2015 12:58:06 +0200",
          },
          "date": "Wed, 02 Sep 2015 12:58:06 GMT",
          "id": 3
        }
      ]

If you know the entry ID, you can query the data directly, i.e.

    > curl http://127.0.0.1:5000/foo/3

returns the same entry as before.


### Query format

The query string consists of one or more items separated by a pipe `|`. Each
item consists of a type tag (either `a` or `d`), a colon `:`, a key, an equal
sign `=` and a value. The type tag specifies if the entries are filtered
according by `a`ttribute or `d`ate. If entries are filtered by date, the key
specifies the relation (`before` or `after`) and the value the time in ISO
format *with* timezone offset. For example, to search for all entries after May
1st 2015, you would query for:

    > curl http://127.0.0.1:5000/foo?q="d:after=2015-04-01+00:00:00+%2B0000"
