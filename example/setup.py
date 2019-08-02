from datetime import datetime
from setuptools import setup, find_packages

setup(
    name='example',
    version=datetime.utcnow().date().isoformat(),
    classifiers=[],
    keywords='',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=['memorious', 'datafreeze'],
    entry_points={
        'memorious.plugins': [
            'example = example:init'
        ]
    }
)
