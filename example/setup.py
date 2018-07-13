from datetime import datetime
from setuptools import setup, find_packages

setup(
    name='crawlers',
    version=datetime.utcnow().date().isoformat(),
    classifiers=[],
    keywords='',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=['memorious', ],
    entry_points={},
    tests_require=[]
)
