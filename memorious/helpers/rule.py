import re
from urllib.parse import urlparse
from pantomime import normalize_mimetype

from memorious.logic.mime import GROUPS


class Rule(object):
    def __init__(self, value):
        self.value = value

    def configure(self):
        pass

    def apply(self, res):
        raise NotImplementedError

    def to_dict(self):
        return self.value

    @staticmethod
    def get_rule(spec):
        if not isinstance(spec, dict):
            raise Exception('Not a valid rule: %r' % spec)
        if len(spec) > 1:
            raise Exception('Ambiguous rules: %r' % spec)
        for rule_name, value in spec.items():
            rule_cls = RULES.get(rule_name)
            if rule_cls is None:
                raise Exception('Unknown rule: %s' % rule_name)
            rule = rule_cls(value)
            rule.configure()
            return rule
        raise Exception('Empty rule: %s' % spec)


class ListRule(Rule):
    """An abstract type of rules that contain a set of other rules."""

    def configure(self):
        if not isinstance(self.value, (list, set, tuple)):
            raise Exception("Not a list: %r", self.value)

    @property
    def children(self):
        for rule in self.value:
            yield self.get_rule(rule)


class OrRule(ListRule):
    """Any nested rule must apply."""

    def apply(self, res):
        for rule in self.children:
            if rule.apply(res):
                return True
        return False


class AndRule(ListRule):
    """All nested rules must apply."""

    def apply(self, res):
        for rule in self.children:
            if not rule.apply(res):
                return False
        return True


class NotRule(Rule):
    """Invert a nested rule."""

    def configure(self):
        self.rule = self.get_rule(self.value)

    def apply(self, res):
        return not self.rule.apply(res)


class MatchAllRule(Rule):
    """Just say yes."""

    def apply(self, res):
        return True


class MimeTypeRule(Rule):

    def configure(self):
        self.clean = normalize_mimetype(self.value)

    def apply(self, res):
        return res.content_type == self.clean


class MimeGroupRule(Rule):

    def apply(self, res):
        if res.content_type.startswith('%s/' % self.value):
            return True
        return res.content_type in GROUPS.get(self.value, [])


class DomainRule(Rule):
    """Match all pages from a particular domain."""

    def clean_domain(self, domain):
        if domain is None:
            return
        pr = urlparse(domain)
        domain = pr.hostname or pr.path
        domain = domain.strip('.').lower()
        return domain

    def configure(self):
        if not isinstance(self.value, str):
            raise Exception("Not a domain: %r", self.value)
        self.domain = self.clean_domain(self.value)
        self.sub_domain = '.%s' % self.domain

    def apply(self, res):
        hostname = self.clean_domain(res.url)
        if hostname is None or self.domain is None:
            return False
        if hostname == self.domain:
            return True
        if hostname.endswith(self.sub_domain):
            return True
        return False


class UrlPatternRule(Rule):

    def configure(self):
        if not isinstance(self.value, str):
            raise Exception("Not a regex: %r", self.value)
        self.pattern = re.compile(self.value, re.I | re.U)

    def apply(self, res):
        if self.pattern.match(res.url):
            return True
        return False


RULES = {}
RULES['or'] = OrRule
RULES['any'] = OrRule
RULES['and'] = AndRule
RULES['all'] = AndRule
RULES['not'] = NotRule
RULES['match_all'] = MatchAllRule
RULES['domain'] = DomainRule
RULES['mime_type'] = MimeTypeRule
RULES['mime_group'] = MimeGroupRule
RULES['pattern'] = UrlPatternRule
