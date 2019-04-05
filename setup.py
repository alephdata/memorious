from setuptools import setup, find_packages

setup(
    name='memorious',
    version='0.11.1',
    description="A minimalistic, recursive web crawling library for Python.",
    long_description="",
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='',
    author='Journalism Development Network',
    author_email='data@occrp.org',
    url='http://github.com/alephdata/memorious',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    package_data={
        'memorious': [
            'migrate/*',
            'migrate/versions/*',
            'migrate/ui/static/*',
            'migrate/ui/templates/*'
        ]
    },
    zip_safe=False,
    install_requires=[
        'banal >= 0.4.2',
        'click',
        'requests[security] >= 2.21.0',
        'requests_ftp',
        'alephclient >= 0.9.0',
        'lxml >= 3',
        'PyYAML >= 3.10',
        'normality >= 1.0.0',
        'tabulate',
        'dataset >= 1.0.8',
        'servicelayer >= 1.0.3',
        'urlnormalizer >= 1.2.0',
        'celestial >= 0.2.0',
        'dateparser',
        'stringcase',
        'python-redis-rate-limit >= 0.0.5',
        'blinker >= 1.4',
        'flask',
        'babel'
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
        ],
        'memorious.operations': [
            'memorious = memorious.cli:main',
            'fetch = memorious.operations.fetch:fetch',
            'dav_index = memorious.operations.fetch:dav_index',
            'session = memorious.operations.fetch:session',
            'parse = memorious.operations.parse:parse',
            'clean_html = memorious.operations.clean:clean_html',
            'aleph_emit = memorious.operations.aleph:aleph_emit',
            'seed = memorious.operations.initializers:seed',
            'sequence = memorious.operations.initializers:sequence',
            'dates = memorious.operations.initializers:dates',
            'enumerate = memorious.operations.initializers:enumerate',
            'inspect = memorious.operations.debug:inspect',
            'documentcloud_query = memorious.operations.documentcloud:documentcloud_query',  # noqa
            'directory = memorious.operations.store:directory',
            'extract = memorious.operations.extract:extract',
            'db = memorious.operations.db:db',
            'ftp_fetch = memorious.operations.ftp:ftp_fetch',
        ]
    },
    extras_require={
        'dev': [
            'pytest',
            'pytest-env',
            'pytest-cov',
            'pytest-mock',
        ]
    }
)
