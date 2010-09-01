#!/usr/bin/env python
#encoding:utf-8
#author:swc/Steve
#project:comicvine_api
#repository:http://github.com/swc/comicvine_api
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

"""Unittests for comicvine_api
Modified from http://github.com/dbr/tvdb_api
"""

import sys
import datetime
import unittest

sys.path.append("..")

import comicvine_api
import comicvine_ui
from comicvine_exceptions import (comicvine_error, comicvine_userabort, comicvine_seriesnotfound,
    comicvine_issuenotfound, comicvine_attributenotfound)

class test_comicvine_basic(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)
     
    def test_different_case(self):
        """Checks the auto-correction of series names is working.
        It should correct the weirdly capitalised 'sMAx' to 'Smax'
        """
        self.assertEquals(self.c['sMAx'][1]['issuename'], None)
        self.assertEquals(self.c['sMAx']['seriesname'], 'Smax')

    def test_spaces(self):
        """Checks seriesnames with spaces
        """
        self.assertEquals(self.c['y: the last man']['seriesname'], 'Y: The Last Man')
        self.assertEquals(self.c['y: the last man'][1]['issuename'], 'Unmanned')

    def test_numeric(self):
        """Checks numeric series names
        """
        self.assertEquals(self.c['300'][1]['issuename'], None)
        self.assertEquals(self.c['300']['seriesname'], 'Archie 3000!')

    def test_series_iter(self):
        """Iterating over a series returns each issue
        """
        self.assertEquals(
            len(
                [issue for issue in self.c['V for Vendetta']]
            ),
            10
        )

    def test_get_series_description(self):
        """Checks series description is retrieved correctly.
        """
        self.assertEquals(
            self.c['Blankets']['description'].find(
                'This title won Thompson the 2004 Eisner Award for Best Writer/Artist') > -1,
            True
        )



class test_comicvine_errors(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)

    def test_seriesnotfound(self):
        """Checks exception is thrown when issue doesn't exist.
        """
        self.assertRaises(comicvine_seriesnotfound, lambda:self.c['the fake series thingy'])
    
    def test_issuenotfound(self):
        """Checks exception is raised for non-existent issue
        """
        self.assertRaises(comicvine_issuenotfound, lambda:self.c['Y: The Last Man'][61])

    def test_attributenamenotfound(self):
        """Checks exception is thrown for if an attribute isn't found.
        """
        self.assertRaises(comicvine_attributenotfound, lambda:self.c['Y: The Last Man'][1]['afakeattributething'])
        self.assertRaises(comicvine_attributenotfound, lambda:self.c['Y: The Last Man']['afakeattributething'])

class test_comicvine_search(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)

    def test_search_len(self):
        """There should be only one result matching
        """
        self.assertEquals(len(self.c['Y: The Last Man'].search('Unmanned Chapter Two')), 1)

    def test_search_checkname(self):
        """Checks you can get the issue name of a search result
        """
        self.assertEquals(self.c['Y: The Last Man'].search('unmanned')[0]['issuename'], 'Unmanned')
        self.assertEquals(self.c['Y: The Last Man'].search('Unmanned Chapter Two')[0]['issuename'], 'Unmanned Chapter Two')
    
    def test_search_multiresults(self):
        """Checks search can return multiple results
        """
        self.assertEquals(len(self.c['Y: The Last Man'].search('Unmanned')) >= 3, True)

    def test_search_no_params_error(self):
        """Checks not supplying search info raises TypeError"""
        self.assertRaises(
            TypeError,
            lambda: self.c['V for Vendetta'].search()
        )
    
    def test_search_series(self):
        """Checks the searching of an entire series"""
        self.assertEquals(
            len(self.c['Y: The Last Man'].search('Unmanned', key='issuename')),
            5
        )

class test_comicvine_data(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)

    def test_issue_publish_month(self):
        """Check the publish month is retrieved
        """
        self.assertEquals(
            self.c['Y: The Last Man'][1]['publish_month'],
            '9'
        )
        
    def test_issue_publish_year(self):
        """Check the publish year is retrieved
        """
        self.assertEquals(
            self.c['Y: The Last Man'][1]['publish_year'],
            '2002'
        )

class test_comicvine_misc(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)

    def test_repr_series(self):
        """Check repr() of Issue
        """
        self.assertEquals(
            repr(self.c['Y: The Last Man']),
            "<Series Y: The Last Man (containing 60 issues)>"
        )
    def test_repr_issue(self):
        """Check repr() of Issue
        """
        self.assertEquals(
            repr(self.c['Y: The Last Man'][1]),
            "<Issue 01 - Unmanned>"
        )

class test_comicvine_credits(unittest.TestCase):
    c = None
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True, credits = True)

    def test_actors_is_correct_datatype(self):
        """Check issue/credits key exists and is correct type"""
        self.assertTrue(
            isinstance(
                self.c['The Walking Dead'][1]['credits'],
                comicvine_api.Credits
            )
        )
    
    def test_actors_has_actor(self):
        """Check issue has at least one Credit
        """
        self.assertTrue(
            isinstance(
                self.c['The Walking Dead'][1]['credits'][0],
                comicvine_api.Credit
            )
        )
    
    def test_actor_has_name(self):
        """Check first credit has a name"""
        self.assertEquals(
            self.c['The Walking Dead'][1]['credits'][0]['name'],
            "Robert Kirkman"
        )

class test_comicvine_doctest(unittest.TestCase):
    # Used to store the cached instance of Comicvine()
    c = None
    
    def setUp(self):
        if self.c is None:
            self.__class__.c = comicvine_api.Comicvine(cache = True)
    
    def test_doctest(self):
        """Check docstring examples works"""
        import doctest
        doctest.testmod(comicvine_api)
#end test_comicvine

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity = 2)
    unittest.main(testRunner = runner)
