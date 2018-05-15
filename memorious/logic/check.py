import numbers
import re
from dateutil.parser import parse


class ContextCheck(object):
    def __init__(self, context):
        self.context = context

    def shout(self, msg, strict=False, *args):
        if strict:
            raise ValueError(msg % args)
        else:
            self.context.log.info(msg, *args)
        
    def is_not_empty(self, value, strict=False):
        """if p is not empty"""
        if value:
            return
        self.shout('Value %r is not empty', strict, value)
        
    def is_numeric(self, value, strict=False):
        """if p is numeric"""
        if value.isnumeric():
            return
        self.shout('value %r is not numeric', strict, value)

    def is_integer(self, value, strict=False):
        """if p is an integer"""
        if isinstance(value, numbers.Number):
            return
        self.shout('value %r is not an integer', strict, value)

    def match_date(self, value, strict=False):
        """if p is a date"""
        if parse(value):
            return
        self.shout('Value %r is not a valid date', strict, value)

    def match_regexp(self, value, q, strict=False):
        """if p matches a regexp q"""
        mr = re.compile(q)
        if mr.match(value):
            return
        self.shout('%r not matching the regexp %r', strict, value, q)

    def has_length(self, value, q, strict=False):
        """if p has a length of q"""
        if len(value) == q:
            return
        self.shout('Value %r not matching length %r', strict, value, q)

    def must_contain(self, value, q, strict=False):
        """if p must contain q"""
        if str(value).find(q):
            return
        self.shout('Value %r does not contain %r', strict, value, q)
