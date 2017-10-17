## Development

### Making a migration

To autogenerate a migration:

```sh
$ cd memorious/migrate
$ alembic revision --autogenerate -m 'message'
```

Then edit to make it actually work and remove surplus changes. We're generally
not aiming to support downgrades.

### Licensing

see ``LICENSE``