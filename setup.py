from setuptools import setup, find_packages

setup(
    name='memorious',
    version='0.4.0',
    description="A minimalistic, recursive web crawling library for Python.",
    long_description="",
    classifiers=[
        "Development Status :: 1 - Alpha",
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
    package_data={},
    zip_safe=False,
    install_requires=[
        'banal',
        'requests[security] >= 2.5',
        'click',
        'lxml >= 3',
        'PyYAML >= 3.10',
        'normality',
        'celery',
        'tabulate',
        'sqlalchemy',
        'dataset',
        'six',
        'storagelayer',
        'urlnorm',
        'werkzeug',
        'fake-useragent',
        'pycountry',
        'countrynames',
        'dateparser',
        'stringcase'
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
        ],
    },
    tests_require=[]
)
