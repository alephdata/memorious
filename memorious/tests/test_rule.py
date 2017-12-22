from collections import namedtuple
import pytest
from memorious.helpers.rule import RULES, Rule, DomainRule, UrlPatternRule


spec = {
    'and': [
        {'domain': 'occrp.org'},
        {'not': {
            'or': [
                {'domain': 'vis.occrp.org'},
                {'domain': 'tech.occrp.org'},
                {'domain': 'data.occrp.org'},
                {'mime_group': 'assets'},
                {'mime_group': 'images'},
                {'pattern': 'https://www.occrp.org/en/component/.*'},
                {'pattern': 'https://www.occrp.org/en/donate.*'},
                {'pattern': 'https://www.occrp.org/.*start=.*'},
                {'pattern': 'https://www.occrp.org/ru/.*'}
            ]
        }}
    ]
}

invalid_spec = {
    "and": [
        {'domain': 'occrp.org'},
        {"not": {'domain': 'vis.occrp.org'}}
    ],
    "not": {'mime_group': 'images'},
}

rule = {}


class TestRule(object):
    def test_get_rule(self):
        with pytest.raises(Exception):
            Rule.get_rule(invalid_spec)
        assert isinstance(Rule.get_rule(spec), RULES["and"])


class TestDomainRule(object):
    def test_domain_rule(self):
        rule = DomainRule("occrp.org")
        rule.configure()
        Response = namedtuple("Response", "url")
        res = Response(url="http://occrp.org")
        assert rule.apply(res)
        res = Response(url="http://not-occrp.org")
        assert rule.apply(res) is False


class TestUrlPatternRule(object):
    def test_url_pattern(self):
        rule = UrlPatternRule("https://www.occrp.org/en/donate.*")
        rule.configure()
        Response = namedtuple("Response", "url")
        res = Response(url="https://www.occrp.org/en/donate.html")
        assert rule.apply(res)
        res = Response(url="http://not-occrp.org")
        assert rule.apply(res) is False
