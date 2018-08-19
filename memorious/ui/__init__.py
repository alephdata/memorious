from memorious.core import init_memorious
from memorious.ui.views import app


init_memorious()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
