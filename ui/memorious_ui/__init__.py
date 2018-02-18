import logging

from memorious import settings
from memorious.core import load_extensions, ensure_db
from memorious_ui.views import app, sentry


ensure_db()
load_extensions()

if settings.SENTRY_DSN:
    sentry.init_app(app,
                    dsn=settings.SENTRY_DSN,
                    logging=True,
                    level=logging.ERROR)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
