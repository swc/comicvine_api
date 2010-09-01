#!/usr/bin/env python
#encoding:utf-8
#author:swc/Steve
#project:comicvine_api
#repository:http://github.com/swc/comicvine_api
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

"""Unit test runner for comicvine_api
Modified from http://github.com/dbr/tvdb_api
"""

import sys
import unittest

import test_comicvine_api

def main():
    suite = unittest.TestSuite([
        unittest.TestLoader().loadTestsFromModule(test_comicvine_api)
    ])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(
        int(main())
    )
