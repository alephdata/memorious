from memorious.core import connect_redis


class Base(object):
    conn = connect_redis()
