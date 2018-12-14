from setuptools import setup, find_packages

setup(
    name='memorious',
    version='0.7.20',
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
        'six',
        'banal',
        'click',
        'requests[security]>=2.18',
        'requests_ftp',
        'alephclient>=0.6.9',
        'lxml>=3',
        'PyYAML>=3.10',
        'normality>=0.6.1',
        'tabulate',
        'dataset>=1.0.8',
        'storagelayer>=0.5.2',
        'urlnormalizer>=1.2.0',
        'celestial>=0.2.0',
        'werkzeug',
        'dateparser',
        'stringcase',
        'python-redis-rate-limit>=0.0.5',
        'redis>=2.10.6,<3',
        'blinker>=1.4',
        'boto3>=1.4.8',
        'fakeredis',
        'flask',
        'babel'
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
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
