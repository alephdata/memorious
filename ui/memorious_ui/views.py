from flask import Flask
from flask import render_template
from babel.numbers import format_number

from memorious_ui.reporting import crawlers_index, global_stats

app = Flask(__name__)


@app.template_filter('number')
def number_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return '-'
    return format_number(s, locale='en_US')

@app.context_processor
def context():
    return global_stats()

@app.route('/')
def index():
    crawlers = crawlers_index()
    return render_template('index.html', crawlers=crawlers)


@app.route('/crawlers/<name>')
def crawler(name):
    return 'I AM A BANANA'
