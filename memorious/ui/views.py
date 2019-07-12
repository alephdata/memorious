import math
from urllib.parse import urlencode
import logging
from flask import Flask, request, redirect
from flask import render_template, abort, url_for
from babel.numbers import format_number
from babel.dates import format_date, format_datetime

from memorious.core import settings, manager, init_memorious
from memorious.model import Event

PAGE_SIZE = 50
app = Flask(__name__)
init_memorious()
if settings.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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
    return {
        'version': settings.VERSION,
        'num_crawlers': len(manager),
        'state_change': state_change
    }


def get_crawler(name):
    crawler = manager.get(name)
    if crawler is None:
        abort(404)
    return crawler


def redirect_crawler(crawler):
    if request.form.get('return') == 'index':
        return redirect(url_for('.index'))
    return redirect(url_for('.crawler', name=crawler.name))


@app.route('/')
def index():
    """Generate a list of all crawlers, alphabetically, with op counts."""
    crawlers = []
    for crawler in manager:
        data = Event.get_counts(crawler)
        data['last_active'] = crawler.last_run
        data['total_ops'] = crawler.op_count
        data['running'] = crawler.is_running
        data['crawler'] = crawler
        crawlers.append(data)
    return render_template('index.html', crawlers=crawlers)


@app.route('/crawlers/<name>')
def crawler(name):
    crawler = get_crawler(name)
    stages = []
    for stage in crawler:
        data = Event.get_stage_counts(crawler, stage)
        data['total_ops'] = stage.op_count
        data['stage'] = stage
        stages.append(data)
    runs = list(crawler.runs)
    for run in runs:
        run.update(Event.get_run_counts(crawler, run['run_id']))
    runs = sorted(runs, key=lambda r: r.get('start'), reverse=True)
    return render_template('crawler.html',
                           crawler=crawler,
                           stages=stages,
                           runs=runs)


@app.route('/crawlers/<name>/events')
def events(name):
    crawler = get_crawler(name)
    page = int(request.args.get('page', 1))
    start = (max(1, page) - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    run_id = request.args.get('run_id')
    level = request.args.get('level')
    stage_name = request.args.get('stage_name')

    if stage_name:
        events = Event.get_stage_events(crawler, stage_name, start, end, level)
    elif run_id:
        events = Event.get_run_events(crawler, run_id, start, end, level)
    else:
        events = Event.get_crawler_events(crawler, start, end, level)
    total = len(events)
    pages = int(math.ceil((float(total) / PAGE_SIZE)))
    return render_template('events.html',
                           crawler=crawler,
                           results=events,
                           page=page,
                           pages=pages)


@app.route('/crawlers/<name>/config')
def config(name):
    crawler = get_crawler(name)
    return render_template('config.html', crawler=crawler)


@app.route('/invoke/<crawler>/run', methods=['POST'])
def crawler_run(crawler):
    crawler = get_crawler(crawler)
    crawler.run()
    return redirect_crawler(crawler)


@app.route('/invoke/<crawler>/cancel', methods=['POST'])
def crawler_cancel(crawler):
    crawler = get_crawler(crawler)
    crawler.cancel()
    return redirect_crawler(crawler)


@app.route('/invoke/<crawler>/flush', methods=['POST'])
def crawler_flush(crawler):
    crawler = get_crawler(crawler)
    crawler.flush()
    return redirect_crawler(crawler)


@app.route('/invoke/<crawler>/flush-events', methods=['POST'])
def crawler_flush_events(crawler):
    crawler = get_crawler(crawler)
    crawler.flush_events()
    return redirect_crawler(crawler)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
