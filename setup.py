from setuptools import setup
setup(
name = 'comicvine_api',
version='1.0',

author='swc/Steve',
description='Interface to comicvine.com',
license='GPLv2',

long_description="""\
An easy to use API interface to www.comicvine.com
Modified from http://github.com/dbr/tvdb_api

Basic usage is:

>>> import comicvine_api
>>> c = comicvine_api.Comicvine()
>>> iss = c['My Name Is Earl'][22]
>>> iss
<Issue 22 - Stole a Badge>
>>> iss['issuename']
u'Stole a Badge'
""",

py_modules = ['comicvine_api', 'comicvine_ui', 'comicvine_exceptions', 'cache'],

classifiers=[
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Multimedia",
    "Topic :: Utilities",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
)
