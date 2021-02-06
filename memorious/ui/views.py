import os
from urllib.parse import urlencode
import logging
from flask import Flask, request, redirect, jsonify
from flask import render_template, abort, url_for
from babel.numbers import format_number
from babel.dates import format_date, format_datetime

from memorious.core import settings, manager, init_memorious
from memorious.model import Crawl

template_folder = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=template_folder)
init_memorious()
log = logging.getLogger(__name__)


@app.template_filter("number")
def number_filter(s, default=""):
    if s is None or s == 0 or not len(str(s)):
        return default
    return format_number(s, locale="en_GB")


@app.template_filter("datetime")
def datetime_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return ""
    return format_datetime(s, locale="en_GB", format="short")


@app.template_filter("date")
def date_filter(s):
    if s is None or s == 0 or not len(str(s)):
        return ""
    return format_date(s, locale="en_GB", format="short")


def state_change(name, value):
    state = [(name, value)]
    for aname, avalue in request.args.items():
        if aname != name:
            state.append((aname, avalue))
    return "?" + urlencode(state)


@app.context_processor
def context():
    return {
        "version": settings.VERSION,
        "num_crawlers": len(manager),
        "state_change": state_change,
    }


def get_crawler(name):
    crawler = manager.get(name)
    if crawler is None:
        abort(404)
    return crawler


def redirect_crawler(crawler):
    if request.form.get("return") == "index":
        return redirect(url_for(".index"))
    return redirect(url_for(".crawler", name=crawler.name))


@app.route("/")
def index():
    """Generate a list of all crawlers, alphabetically, with op counts."""
    crawlers = []
    for crawler in manager:
        data = {"crawler": crawler}
        data["last_active"] = crawler.last_run
        data["total_ops"] = crawler.op_count
        data["running"] = crawler.is_running
        data["crawler"] = crawler
        crawlers.append(data)
    return render_template("index.html", crawlers=crawlers)


@app.route("/crawlers/<name>")
def crawler(name):
    crawler = get_crawler(name)
    stages = []
    for stage in crawler:
        data = {"stage": stage}
        data["total_ops"] = stage.op_count
        stages.append(data)
    runs = list(crawler.runs)
    runs = sorted(runs, key=lambda r: r.get("start"), reverse=True)
    return render_template("crawler.html", crawler=crawler, stages=stages, runs=runs)


@app.route("/crawlers/<name>/config")
def config(name):
    crawler = get_crawler(name)
    return render_template("config.html", crawler=crawler)


@app.route("/invoke/<crawler>/run", methods=["POST"])
def crawler_run(crawler):
    crawler = get_crawler(crawler)
    crawler.run()
    return redirect_crawler(crawler)


@app.route("/invoke/<crawler>/cancel", methods=["POST"])
def crawler_cancel(crawler):
    crawler = get_crawler(crawler)
    crawler.cancel()
    return redirect_crawler(crawler)


@app.route("/invoke/<crawler>/flush", methods=["POST"])
def crawler_flush(crawler):
    crawler = get_crawler(crawler)
    crawler.flush()
    return redirect_crawler(crawler)


@app.route("/invoke/<crawler>/change-schedule", methods=["POST"])
def crawler_change_schedule(crawler):
    crawler = get_crawler(crawler)
    schedule = request.json.get("schedule", crawler.schedule)
    Crawl.set_schedule(crawler, schedule)
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
