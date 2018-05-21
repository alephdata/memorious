from setuptools import setup, find_packages

setup(
    name='memorious',
    version='0.5.5',
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
    package_data={'memorious': ['migrate/*', 'migrate/versions/*']},
    zip_safe=False,
    install_requires=[
        'banal',
        'requests[security] >= 2.5',
        'requests_ftp',
        'click',
        'lxml >= 3',
        'PyYAML >= 3.10',
        'normality >= 0.5.7',
        'celery',
        'tabulate',
        'sqlalchemy',
        'dataset >= 1.0.8',
        'six',
        'storagelayer >= 0.3.2',
        'urlnormalizer >= 1.2.0',
        'celestial >= 0.2.0',
        'werkzeug',
        'pycountry',
        'countrynames',
        'dateparser',
        'stringcase',
        'raven',
        'python-redis-rate-limit == 0.0.5',
        'redis == 2.10.6',
        'blinker == 1.4',
        'boto3 == 1.4.8',
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
        ],
        'memorious.plugins': [
            'reporting = memorious.reporting:init'
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
