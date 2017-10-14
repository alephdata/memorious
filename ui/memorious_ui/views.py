from flask import Flask, jsonify
from flask import render_template, abort
from babel.numbers import format_number
from babel.dates import format_date

from memorious_ui.reporting import crawlers_index, global_stats
from memorious_ui.reporting import get_crawler, crawler_stages, crawler_events

app = Flask(__name__)


@app.template_filter('number')
def number_filter(s, default=''):
    if s is None or s == 0 or not len(str(s)):
        return default
    return format_number(s, locale='en_GB')


@app.template_filter('datetime')
def datetime_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return ''
    return format_date(s, locale='en_GB', format='short')


@app.context_processor
def context():
    return global_stats()


@app.route('/')
def index():
    crawlers = crawlers_index()
    return render_template('index.html', crawlers=crawlers)


@app.route('/crawlers/<name>')
def crawler(name):
    crawler = get_crawler(name)
    if crawler is None:
        abort(404)
    stages = crawler_stages(crawler)
    return render_template('crawler.html', crawler=crawler, stages=stages)


@app.route('/crawlers/<name>/events')
def events(name):
    crawler = get_crawler(name)
    if crawler is None:
        abort(404)
    events = crawler_events(crawler)
    return render_template('events.html', crawler=crawler, stages=events)


@app.route('/crawlers/<name>/config')
def config(name):
    crawler = get_crawler(name)
    if crawler is None:
        abort(404)
    return render_template('config.html', crawler=crawler)


@app.route('/invoke/<crawler>/<action>', methods=['POST'])
def invoke(crawler, action):
    crawler = get_crawler(crawler)
    if crawler is None:
        abort(400)
    if action == 'run':
        crawler.run()
        return jsonify({'status': 'ok'})
    else:
        abort(400)
