from setuptools import setup, find_packages

setup(
    name='memorious-ui',
    version='0.0.1',
    description="UI for alephdata/memorious",
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
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
        'memorious',
        'flask',
        'babel'
    ],
    entry_points={
        'console_scripts': [
            'memorious = memorious.cli:main'
        ],
    },
    tests_require=[]
)
