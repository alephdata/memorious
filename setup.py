from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

setup(
    name="memorious",
    version="2.6.2",
    description="A minimalistic, recursive web crawling library for Python.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords="",
    author="Organized Crime and Corruption Reporting Project",
    author_email="data@occrp.org",
    url="http://github.com/alephdata/memorious",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    namespace_packages=[],
    include_package_data=True,
    package_data={
        "memorious": [
            "migrate/*",
            "migrate/versions/*",
            "migrate/ui/static/*",
            "migrate/ui/templates/*",
        ]
    },
    zip_safe=False,
    install_requires=[
        "banal >= 1.0.1, < 2.0.0",
        "click",
        "requests[security] >= 2.21.0",
        "PySocks == 1.7.1",
        "requests_ftp",
        "lxml >= 4",
        "normality >= 2.1.1, < 3.0.0",
        "tabulate",
        "python-dateutil >= 2.8.2, < 3.0.0",
        "dataset >= 1.0.8",
        "servicelayer[google,amazon] == 1.20.7",
        "pantomime == 0.5.1",
        "alephclient >= 2.3.5",
        "followthemoney >= 2.3.1",
        "followthemoney-store >= 3.0.1",
        "dateparser",
        "stringcase",
        "flask",
        "babel",
    ],
    entry_points={
        "console_scripts": ["memorious = memorious.cli:main"],
        "memorious.operations": [
            "memorious = memorious.cli:main",
            "fetch = memorious.operations.fetch:fetch",
            "session = memorious.operations.fetch:session",
            "dav_index = memorious.operations.webdav:dav_index",
            "parse = memorious.operations.parse:parse",
            "clean_html = memorious.operations.clean:clean_html",
            "seed = memorious.operations.initializers:seed",
            "tee = memorious.operations.initializers:tee",
            "sequence = memorious.operations.initializers:sequence",
            "dates = memorious.operations.initializers:dates",
            "enumerate = memorious.operations.initializers:enumerate",
            "inspect = memorious.operations.debug:inspect",
            "documentcloud_query = memorious.operations.documentcloud:documentcloud_query",  # noqa
            "documentcloud_mark_processed = memorious.operations.documentcloud:documentcloud_mark_processed",  # noqa
            "directory = memorious.operations.store:directory",
            "cleanup_archive = memorious.operations.store:cleanup_archive",
            "extract = memorious.operations.extract:extract",
            "db = memorious.operations.db:db",
            "ftp_fetch = memorious.operations.ftp:ftp_fetch",
            "aleph_emit = memorious.operations.aleph:aleph_emit",
            "aleph_emit_document = memorious.operations.aleph:aleph_emit_document",
            "aleph_folder = memorious.operations.aleph:aleph_folder",
            "aleph_emit_entity = memorious.operations.aleph:aleph_emit_entity",
            "balkhash_put = memorious.operations.ftm:ftm_store",
            "ftm_store = memorious.operations.ftm:ftm_store",
            "ftm_load_aleph = memorious.operations.ftm:ftm_load_aleph",
        ],
    },
    extras_require={
        "dev": [
            "pytest",
            "pytest-env",
            "pytest-cov",
            "pytest-mock",
            "sphinx",
            "sphinx_rtd_theme",
            "recommonmark",
        ],
        "ocr": [
            "tesserocr",
        ],
    },
)
