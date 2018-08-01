import logging

from memorious import settings
from memorious.core import init_memorious
from memorious.ui.views import app, sentry


init_memorious()
if settings.SENTRY_DSN:
    sentry.init_app(app,
                    dsn=settings.SENTRY_DSN,
                    logging=True,
                    level=logging.ERROR)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
