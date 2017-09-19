from setuptools import setup, find_packages

setup(
    name='memorious',
    version='0.3.0',
    description="A minimalistic, recursive web crawling library for Python.",
    long_description="",
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='',
    author='Lion Summerbell',
    author_email='lion@occrp.org',
    url='http://github.com/alephdata/memorious',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'banal',
        'requests >= 2.5',
        'click',
        'lxml >= 3',
        'PyYAML >= 3.10',
        'normality',
        'pyicu',
        'celery',
        'tabulate',
        'sqlalchemy',
        'dataset',
        'six',
        'storagelayer',
        'psycopg2',
        'urlnorm',
        'werkzeug',
        'fake-useragent',
        'pycountry',
        'countrynames'
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
        ],
    },
    tests_require=[]
)
