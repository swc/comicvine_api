#!/usr/bin/env python
#encoding:utf-8
#author:swc/Steve
#project:comicvine_api
#repository:http://github.com/swc/comicvine_api
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

"""Simple-to-use Python interface to Comic Vine's API (www.comicvine.com)
Modified from http://github.com/dbr/tvdb_api

Example usage:

>>> from comicvine_api import Comicvine
>>> c = Comicvine()
>>> c['Y: The Last Man'][1]['issuename']
'Unmanned'
"""
__author__ = "swc/Steve"
__version__ = "1.02"

import os
import re
import sys
import urllib
import urllib2
import StringIO
import tempfile
import warnings
import logging
import datetime

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

try:
    import gzip
except ImportError:
    gzip = None


from cache import CacheHandler

from comicvine_ui import BaseUI, ConsoleUI
from comicvine_exceptions import (comicvine_error, comicvine_userabort, comicvine_seriesnotfound,
    comicvine_issuenotfound, comicvine_attributenotfound)

lastTimeout = None

def log():
    return logging.getLogger("comicvine_api")

def levenshtein_distance(first, second):
    """Find the Levenshtein distance between two strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
       distance_matrix[i][0] = i
    for j in range(second_length):
       distance_matrix[0][j]=j
    for i in xrange(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]
    
class SeriesContainer(dict):
    """Simple dict that holds a collection of Series instances
    """
    pass

class Series(dict):
    """Holds a dict of issues, and series data.
    """
    def __init__(self):
        dict.__init__(self)
        self.data = {}

    def __repr__(self):
        return "<Series %s (containing %s issues)>" % (
            self.data.get(u'seriesname', 'instance'),
            len(self)
        )

    def __getitem__(self, key):
        if key in self:
            # Key is an issue, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for series-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Issue number x was not found
            raise comicvine_issuenotfound("Could not find issue %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise comicvine_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term = None, key = None):
        """
        Search all issues in series. Can search all data, or a specific key (for
        example, issuename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Issue() instance, so doing
        search_results[0]['issuename'] will retrieve the issue name of the
        first match.

        Search terms are converted to lower case (unicode) strings.

        # Examples
        
        These examples assume c is an instance of Comicvine():
        
        >>> c = Comicvine()
        >>>

        To search for all issues of "Y: The Last Man" with a bit of data
        containing "man":

        >>> c['Y: The Last Man'].search("Yorick")
        [<Issue 01 - Unmanned>]
        >>>

        Search for "Y: The Last Man" issue named "Safeword":

        >>> c['Y: The Last Man'].search('Safeword', key = 'issuename')
        [<Issue 01 - Safeword>]
        >>>

        To search "Y: The Last Man" for all issues with "man" in the issue name:

        >>> c['Y: The Last Man'].search('man', key = 'issuename')
        [<Issue 01x02 - My Mentor>, <Issue 03x15 - My Tormented Mentor>]
        >>>

        # Using search results

        >>> results = c['Y: The Last Man'].search("Unman")
        >>> print results[0]['issuename']
        Unmanned
        >>> for x in results: print x['issuename']
        Unmanned
        >>>
        """
        results = []
        for iss in self.values():
            searchresult = iss.search(term = term, key = key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results


class Issue(dict):
    def __repr__(self):
        issno = float(self.get(u'issue_number', 0))
        issname = self.get(u'issuename')
        if issname is not None:
            return "<Issue %02d - %s>" % (issno, issname)
        else:
            return "<Issue %02d>" % (issno)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
        	raise comicvine_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term = None, key = None):
        """Search issue data for term, if it matches, return the Issue (self).
        The key parameter can be used to limit the search to a specific element,
        for example, issuename.
        
        This primarily for use use by Series.search. See
        Series.search for further information on search

        Simple example:

        >>> i = Issue()
        >>> i['issuename'] = "An Example"
        >>> i.search("examp")
        <Issue 01 - An Example>
        >>>

        Limiting by key:

        >>> i.search("examp", key = "issuename")
        <Issue 01 - An Example>
        >>>
        """
        if term == None:
            raise TypeError("must supply string to search for (contents)")

        term = unicode(term).lower()
        for cur_key, cur_value in self.items():
            cur_key, cur_value = unicode(cur_key).lower(), unicode(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find( unicode(term).lower() ) > -1:
                return self
            #end if cur_value.find()
        #end for cur_key, cur_value


class Credits(list):
    """Holds all Credit instances for an issue
    """
    pass


class Credit(dict):
    """Represents a single credit. Should contain..

    id,
    name,
    role
    """
    def __repr__(self):
        return "<Credit \"%s\">" % (self.get("name"))


class Comicvine:
    """Create easy-to-use interface to name of issue
    >>> c = Comicvine()
    >>> c['Y: The Last Man'][1]['issuename']
    'Unmanned'
    """
    def __init__(self,
                interactive = False,
                select_first = False,
                debug = False,
                cache = True,
                credits = False,
                custom_ui = None,
                apikey = None,
                forceConnect=False):
        """interactive (True/False):
            When True, uses built-in console UI is used to select the correct series.
            When False, the first search result is used.

        select_first (True/False):
            Automatically selects the first series search result (rather
            than showing the user a list of more than one series).
            Is overridden by interactive = False, or specifying a custom_ui

        debug (True/False) DEPRECATED:
             Replaced with proper use of logging module. To show debug messages:

                 >>> import logging
                 >>> logging.basicConfig(level = logging.DEBUG)

        cache (True/False/str/unicode):
            Retrieved XML are persisted to to disc. If true, stores in comicvine_api
            folder under your systems TEMP_DIR, if set to str/unicode instance it
            will use this as the cache location. If False, disables caching.

        credits (True/False):
            Retrieves a list of the credits for a series. These are accessed
            via the credits key of a Series(), for example:

            >>> c = Comicvine(credits=True)
            >>> c['Y: The Last Man']['credits'][0]['name']
            u'Zach Braff'

        custom_ui (comicvine_ui.BaseUI subclass):
            A callable subclass of comicvine_ui.BaseUI (overrides interactive option)
        
        apikey (str/unicode):
            Override the default comicvine.com API key. By default it will use
            comicvine_api's own key (fine for small scripts), but you can use your
            own key if desired - this is recommended if you are embedding
            comicvine_api in a larger application)
            See http://comicvine.com/?tab=apiregister to get your own key

        forceConnect (bool):
            If true it will always try to connect to theTVDB.com even if we
            recently timed out. By default it will wait one minute before
            trying again, and any requests within that one minute window will
            return an exception immediately. 
        """
        
        global lastTimeout
        
        # if we're given a lastTimeout that is less than 1 min just give up
        if not forceConnect and lastTimeout != None and datetime.datetime.now() - lastTimeout < datetime.timedelta(minutes=1):
            raise comicvine_error("We recently timed out, so giving up early this time")
        
        self.series = SeriesContainer() # Holds all Series classes
        self.corrections = {} # Holds series-name to series_id mapping

        self.config = {}

        if apikey is not None:
            self.config['apikey'] = apikey
        else:
            self.config['apikey'] = "630af825c6c615476f9f89cac4ba0d232c434e90" # comicvine_api's API key

        self.config['debug_enabled'] = debug # show debugging messages

        self.config['custom_ui'] = custom_ui

        self.config['interactive'] = interactive # prompt for correct series?

        self.config['select_first'] = select_first

        if cache is True:
            self.config['cache_enabled'] = True
            self.config['cache_location'] = self._getTempDir()
        elif isinstance(cache, basestring):
            self.config['cache_enabled'] = True
            self.config['cache_location'] = cache
        else:
            self.config['cache_enabled'] = False

        if self.config['cache_enabled']:
            self.urlopener = urllib2.build_opener(
                CacheHandler(self.config['cache_location'])
            )
        else:
            self.urlopener = urllib2.build_opener()

        self.config['credits_enabled'] = credits

        if self.config['debug_enabled']:
            warnings.warn("The debug argument to comicvine_api.__init__ will be removed in the next version. "
            "To enable debug messages, use the following code before importing: "
            "import logging; logging.basicConfig(level=logging.DEBUG)")
            logging.basicConfig(level=logging.DEBUG)

        # The following url_ configs are based of the
        # http://comicvine.com/wiki/index.php/Programmers_API
        self.config['base_url'] = "http://api.comicvine.com"

        self.config['url_getSeries'] = u"%(base_url)s/search/?api_key=%(apikey)s&query=%%s&resources=volume&offset=%%s&field_list=name,id" % self.config

        self.config['url_issInfo'] = u"%(base_url)s/issue/%%s/?api_key=%(apikey)s" % self.config

        self.config['url_seriesInfo'] = u"%(base_url)s/volume/%%s/?api_key=%(apikey)s" % self.config

        self.config['url_siteDetail'] = u"%%s?sort=issue_number&page=%%s" % self.config

    #end __init__

    def _getTempDir(self):
        """Returns the [system temp dir]/comicvine_api
        """
        return os.path.join(tempfile.gettempdir(), "comicvine_api")

    def _loadUrl(self, url, recache = False):
        global lastTimeout
        try:
            log().debug("Retrieving URL %s" % url)
            resp = self.urlopener.open(url)
            if 'x-local-cache' in resp.headers:
                log().debug("URL %s was cached in %s" % (
                    url,
                    resp.headers['x-local-cache'])
                )
                if recache:
                    log().debug("Attempting to recache %s" % url)
                    resp.recache()
        except (IOError, urllib2.URLError), errormsg:
            if not str(errormsg).startswith('HTTP Error'):
                lastTimeout = datetime.datetime.now()
            raise comicvine_error("Could not connect to server: %s" % (errormsg))
        #end try
        
        # handle gzipped content,
        # http://dbr.lighthouseapp.com/projects/13342/tickets/72-gzipped-data-patch
        if 'gzip' in resp.headers.get("Content-Encoding", ''):
            if gzip:
                stream = StringIO.StringIO(resp.read())
                gz = gzip.GzipFile(fileobj=stream)
                return gz.read()
            
            raise comicvine_error("Received gzip data from comicvine.com, but could not correctly handle it")
        
        #print resp.read()
        return resp.read()

    def _getetsrc(self, url):
        """Loads a URL using caching, returns an ElementTree of the source
        """
        src = self._loadUrl(url)
        try:
            return ElementTree.fromstring(src)
        except SyntaxError:
            src = self._loadUrl(url, recache=True)
            try:
                return ElementTree.fromstring(src)
            except SyntaxError, exceptionmsg:
                errormsg = "There was an error with the XML retrieved from comicvine.com:\n%s" % (
                    exceptionmsg
                )

                if self.config['cache_enabled']:
                    errormsg += "\nFirst try emptying the cache folder at..\n%s" % (
                        self.config['cache_location']
                    )

                errormsg += "\nIf this does not resolve the issue, please try again later. If the error persists, report a bug on"
                errormsg += "\nhttp://dbr.lighthouseapp.com/projects/13342-comicvine_api/overview\n"
                raise comicvine_error(errormsg)
    #end _getetsrc

    def _setItem(self, sid, iss, attrib, value):
        """Creates a new issue, creating Series() and
        Issue()s as required. Called by _getSeriesData to populate series

        Since the nice-to-use comicvine[1][24]['name] interface
        makes it impossible to do comicvine[1][24]['name] = "name"
        and still be capable of checking if an issue exists
        so we can raise comicvine_seriesnotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling comicvine[1][24]['issuename'] = "name"
        calls __getitem__ on comicvine[1], there is no way to check if
        comicvine.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.series:
            self.series[sid] = Series()
        if iss not in self.series[sid]:
            self.series[sid][iss] = Issue()
        self.series[sid][iss][attrib] = value
    #end _set_item

    def _setSeriesData(self, sid, key, value):
        """Sets self.series[sid] to a new Series instance, or sets the data
        """
        if sid not in self.series:
            self.series[sid] = Series()
        self.series[sid].data[key] = value

    def _cleanData(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """
        data = data.replace(u"&amp;", u"&")
        data = data.strip()
        return data
    #end _cleanData

    def _getSeries(self, seriesname):
        """This searches TheTVDB.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        print seriesname
        seriesnameclean = urllib.quote(seriesname.encode("utf-8"))
        log().debug("Searching for series %s" % seriesnameclean)
        
        offset = -20
        limit = 20
        resultcount = 1
        allSeries = []
        
        while (offset + limit < resultcount):
	    	offset = offset + 20
	    	seriesEt = self._getetsrc(self.config['url_getSeries'] % (seriesnameclean, offset))
	    	serieslist = seriesEt.findall("results/volume")
	    	
	    	for series in serieslist:
	    	    resultcount = resultcount + 1
	    	    result = dict((k.tag.lower(), k.text) for k in series.getchildren())
	    	    result['id'] = int(result['id'])
	    	    result['seriesname'] = result['name']
	    	    result['match_score'] = levenshtein_distance( seriesname, result['seriesname'] )
	    	    log().debug('Found series %(seriesname)s' % result)
	    	    allSeries.append(result)
	    	#end for series
	    #end while
        
        from operator import itemgetter
        allSeriesSorted = sorted(allSeries, key=itemgetter('match_score'))
			
        if len(allSeries) == 0:
            log().debug('Series result returned zero')
            raise comicvine_seriesnotfound("Series-name search returned zero results (cannot find series on Comic Vine)")

        if self.config['custom_ui'] is not None:
            log().debug("Using custom UI %s" % (repr(self.config['custom_ui'])))
            ui = self.config['custom_ui'](config = self.config)
        else:
            if not self.config['interactive']:
                log().debug('Auto-selecting first search result using BaseUI')
                ui = BaseUI(config = self.config)
            else:
                log().debug('Interactively selecting series using ConsoleUI')
                ui = ConsoleUI(config = self.config)
            #end if config['interactive]
        #end if custom_ui != None

        return ui.selectSeries(allSeriesSorted)

    #end _getSeries

    def _parseCredits(self, sid, iid, creditsEt):
        """Parsers credits XML, from
        http://www.comicvine.com/api/[APIKEY]/volume/[SERIES ID]/credits.xml

        Credits are retrieved using c['series name]['credits'], for example:

        >>> c = Comicvine(credits = True)
        >>> credits = c['The Walking Dead'][1]['credits']
        >>> type(credits)
        <class 'comicvine_api.Credits'>
        >>> type(credits[0])
        <class 'comicvine_api.Credit'>
        >>> credits[1]
        <Credit "Tony Moore">
        >>> sorted(credits[0].keys())
        ['id', 'image', 'name', 'role', 'sortorder']
        >>> credits[1]['name']
        u'Tony Moore'

        Any key starting with an underscore has been processed (not the raw
        data from the XML)
        """
        log().debug("Getting credits for %s - %s" % (sid, iid))

        cur_credits = Credits()
        for curCreditItem in creditsEt.findall("person"):
            curCredit = Credit()
            for curInfo in curCreditItem:
                tag = curInfo.tag.lower()
                value = curInfo.text
                curCredit[tag] = value
            cur_credits.append(curCredit)
        self._setItem(sid, iid, 'credits', cur_credits)

    def _getSeriesData(self, sid):
        """Takes a series ID, gets the issInfo URL and parses the TVDB
        XML file into the series dict in layout:
        series[series_id][issue_number]
        """

        # Parse series information
        log().debug('Getting all series data for %s' % (sid))
        seriesInfoEt = self._getetsrc(
            self.config['url_seriesInfo'] % (sid)
        )
        result = seriesInfoEt.findall("results")[0]
        for curInfo in result:
            tag = curInfo.tag.lower()
            value = curInfo.text

            #value = self._cleanData(value)

            self._setSeriesData(sid, tag, value)
        #end for series
        self._setSeriesData(sid, 'seriesname', result.find('name').text)

            
        #Get issue details
        log().debug('Getting all issues of %s' % (sid))
        
        page=1
        siteDetailUrl=result.find('site_detail_url').text
        siteDetailSrc = self._loadUrl( self.config['url_siteDetail'] % (siteDetailUrl, page) )
        m = re.search('http://www.comicvine.com/(?P<volName>.*)/49-',siteDetailUrl)
        volumeTag=m.group('volName')
        
        m = re.search('page=(?P<last>\d*)&amp;sort=issue_number\">Last</a>',siteDetailSrc)
        
        if hasattr(m, "last"):
            last=int(m.group('last'))
        else:
            last=1

        while (page < last):
        	page = page + 1
        	log().debug('Loading site detail page %d' % (page))
        	siteDetailSrc = siteDetailSrc + self._loadUrl( self.config['url_siteDetail'] % (siteDetailUrl, page) )
        	
        for m in re.finditer('(?ms)<div class=\"comic-container">.*?/37-(?P<iss_id>\d*)/.*?<span class=\"issue\">Issue #(?P<iss_no>\d*)</span>.*?</div>',siteDetailSrc):
            iss_id = int(m.group('iss_id'))
            iss_no = float(m.group('iss_no'))

            self._setItem(sid, iss_no, 'id', iss_id)
            self._setItem(sid, iss_no, 'issue_number', iss_no)
                
            # Parse credits
            #if self.config['credits_enabled']:
            #    self._parseCredits(sid, iss_no, issueresult.find('person_credits'))
        #end for cur_iss
        
        issues=result.find('issues')
        for curIssue in issues:
        	iss_id=int(curIssue.find('id').text)
        	iss_no=self.series[sid].search(iss_id, key='id')[0]['issue_number']
        	self._setItem(sid, iss_no, 'issuename', curIssue.find('name').text)
    #end _getSeriesData

    def _nameToSid(self, name):
        """Takes series name, returns the correct series ID (if the series has
        already been grabbed), or grabs all issues and returns
        the correct SID.
        """
        if name in self.corrections:
            log().debug('Correcting %s to %s' % (name, self.corrections[name]) )
            sid = self.corrections[name]
        else:
            log().debug('Getting series %s' % (name))
            selected_series = self._getSeries( name )
            sname, sid = selected_series['seriesname'], selected_series['id']
            log().debug('Got %(seriesname)s, id %(id)s' % selected_series)

            self.corrections[name] = sid
            self._getSeriesData(selected_series['id'])
        #end if name in self.corrections
        return sid
    #end _nameToSid

    def __getitem__(self, key):
        """Handles comicvine_instance['seriesname'] calls.
        The dict index should be the series id
        """
        if isinstance(key, (int, long)):
            # Item is integer, treat as series id
            if key not in self.series:
                self._getSeriesData(key)
            return self.series[key]
        
        key = key.lower() # make key lower case
        sid = self._nameToSid(key)
        log().debug('Got series id %s' % (sid))
        return self.series[sid]
    #end __getitem__

    def __repr__(self):
        return str(self.series)
    #end __repr__
#end Comicvine

def main():
    """Simple example of using comicvine_api - it just
    grabs an issue name interactively.
    """
    import logging
    logging.basicConfig(level=logging.DEBUG)

    c = Comicvine(interactive=True, cache=False, credits=False)

    print c['air']
    
if __name__ == '__main__':
    main()
