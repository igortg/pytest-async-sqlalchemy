# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import setup

readme_file = Path('README.md')


setup(
    name='pytest-async-sqlalchemy',
    version='0.1.2',
    author='Igor T. Ghisi',
    author_email='igor.ghisi@gmail.com',
    maintainer='Igor T. Ghisi',
    maintainer_email='igor.ghisi@gmail.com',
    license='MIT',
    url='https://github.com/igortg/pytest-async-sqlalchemy',
    description='Database testing fixtures using the SQLAlchemy asyncio API',
    long_description=readme_file.read_text(),
    long_description_content_type="text/markdown",
    py_modules=['pytest_async_sqlalchemy'],
    python_requires='>=3.6',
    install_requires=['pytest>=6.0.0', 'sqlalchemy>=1.4.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'async-sqlalchemy = pytest_async_sqlalchemy',
        ],
    },
)
