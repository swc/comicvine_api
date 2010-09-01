# `comicvine_api`
# Modified from `tvdb_api'

`comicvine_api` is an easy to use interface to [comicvine.com][comicvine]

## To install

You can easily install `comicvine_api` via `easy_install`

    easy_install comicvine_api

You may need to use sudo, depending on your setup:

    sudo easy_install comicvine_api


## Basic usage

    import comicvine_api
    c = comicvine_api.Comicvine()
    issue = c['Y: The Last Man'][1] # get issue 1 of the series 'Y: The Last Man'
    print issue['issuename'] # Print issue name

## Advanced usage

Most of the documentation is in docstrings. The examples are tested (using doctest) so will always be up to date and working.

The docstring for `Comicvine.__init__` lists all initialisation arguments, including support for non-English searches, custom "Select Series" interfaces and enabling the retrieval of credit information. You can also override the default API key using `apikey`, recommended if you're using `comicvine_api` in a larger script or application

### Exceptions

There are several exceptions you may catch, these can be imported from `comicvine_api`:

- `comicvine_error` - this is raised when there is an error communicating with [www.thecomicvine.com][comicvine] (a network error most commonly)
- `comicvine_userabort` - raised when a user aborts the Select Series dialog (by `ctrl+c`, or entering `q`)
- `comicvine_seriesnotfound` - raised when `c['series name']` cannot find anything
- `comicvine_issuenotfound` - raised when the requested issue (`c['series name'][1]`) does not exist.
- `comicvine_attributenotfound` - raised when the requested attribute is not found (`c['series name']['an attribute']` or ``c['series name'][1]['an attribute']``)

### Series data

All data exposed by [thecomicvine.com][comicvine] is accessible via the `Series` class. A Series is retrieved by doing..

    >>> import comicvine_api
    >>> c = comicvine_api.Comicvine()
    >>> series = c['Y: The Last Man']
    >>> type(series)
    <class 'comicvine_api.Series'>

For example, to find out the series name of Y: The Last Man:

    >>> c['Y: The Last Man']['seriesname']
    u'Y: The Last Man'

The data is stored in an attribute named `data`, within the Series instance:

    >>> c['Y: The Last Man'].data.keys()
    ['site_detail_url', 'deck', 'image', 'start_year', 'seriesname', 'character_credits', 'id', 'issues', 'aliases', 'object_credits', 'last_issue', 'team_credits', 'date_last_updated', 'description', 'location_credits', 'api_detail_url', 'date_added', 'first_issue', 'publisher', 'name', 'concept_credits', 'person_credits', 'count_of_issues']

Although each element is also accessible via `c['Y: The Last Man']` for ease-of-use:

    >>> c['Y: The Last Man']['seriesname']
    u'Y: The Last Man'

This is the recommended way of retrieving "one-off" data (for example, if you are only interested in "seriesname"). If you wish to iterate over all data, or check if a particular series has a specific piece of data, use the `data` attribute,

    >>> 'rating' in c['Y: The Last Man'].data
    True

### Credits

Since credit details are separate api calls, retrieving them by default is undesirable. If you wish to retrieve credits, use the `credits` Comicvine initialisation argument:

    >>> c = Comicvine(credits = True)
    >>> credits = c['The Walking Dead'][1]['credits']
    >>> credits[1]
    <Credit "Tony Moore">

Remember a simple list of credits is accessible via the default Series data:

    >>> c['The Walking Dead']['credits']
    u'|Robert Kirkman|Charlie Adlard|Tony Moore|'

[comicvine]: http://www.thecomicvine.com