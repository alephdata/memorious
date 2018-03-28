from urllib import urlencode

from flask import Flask, jsonify, request
from flask import render_template, abort
from babel.numbers import format_number
from babel.dates import format_date, format_datetime
from raven.contrib.flask import Sentry

from memorious.core import session
from memorious_ui.reporting import (
    crawlers_index, global_stats, get_crawler,
    crawler_stages, crawler_events,
    crawler_runs
)

app = Flask(__name__)
sentry = Sentry()


@app.after_request
def cleanup(response):
    session.remove()
    return response


@app.template_filter('number')
def number_filter(s, default=''):
    if s is None or s == 0 or not len(str(s)):
        return default
    return format_number(s, locale='en_GB')


@app.template_filter('datetime')
def datetime_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return ''
    return format_datetime(s, locale='en_GB', format='short')


@app.template_filter('date')
def date_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return ''
    return format_date(s, locale='en_GB', format='short')


def state_change(name, value):
    state = [(name, value)]
    for aname, avalue in request.args.items():
        if aname != name:
            state.append((aname, avalue))
    return '?' + urlencode(state)


@app.context_processor
def context():
    context = global_stats()
    context['state_change'] = state_change
    return context


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
    runs = crawler_runs(crawler)
    return render_template('crawler.html',
                           crawler=crawler,
                           stages=stages, runs=runs)


@app.route('/crawlers/<name>/events')
def events(name):
    crawler = get_crawler(name)
    if crawler is None:
        abort(404)
    events = crawler_events(crawler,
                            page=int(request.args.get('page', 1)),
                            run_id=request.args.get('run_id'),
                            level=request.args.get('level'),
                            stage=request.args.get('stage'))
    return render_template('events.html',
                           crawler=crawler,
                           events=events)


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
    if action == 'flush':
        crawler.flush()
        return jsonify({'status': 'ok'})
    else:
        abort(400)
