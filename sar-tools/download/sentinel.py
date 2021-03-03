"""
Tools for downloading Sentinel-1 SAR data using the [Copernicus Open Access API.](https://scihub.copernicus.eu/twiki/do/view/SciHubWebPortal/APIHubDescription)

"""

import requests
import xmltodict
import getpass
import datetime

class CopernicusHub:
    """
    Connects to the [Copernicus open access hub](https://scihub.copernicus.eu/twiki/do/view/SciHubWebPortal/APIHubDescription)
    provided by the European Space Agency (ESA).

    ARGUMENTS:
        username (string): Your Copernicus username
        password (string): Your Copernicus password.  Note that you should not
            store this in your code.  Instead, use the standard python
            getpass() function to enter the password.
    """

    def __init__(self, username, password):
        self._user = username
        self._pass = password
        self._url_search = 'https://scihub.copernicus.eu/dhus/search'
        self._url_data = 'https://scihub.copernicus.eu/dhus/odata/v1'
        self._platform  = 'Sentinel-1'

    def _GetQueryString(self, opts):
        """ Processes optional arguments passed to the "Search" function to
            construct the query string required by the copernicus API.
        """
        qString = 'platformname:'+self._platform

        # Process the optioons into the query string
        if 'type' in opts:
            typestr = opts['type']
            assert(typestr in ['SLC','GRD','OCN'])
            qString += ' AND producttype:' + typestr


        if ('end_date' in opts or 'start_date' in opts):
            end_str = 'NOW'
            start_str = '2000-01-01T00:00:00.000Z'

            if 'end_date' in opts:
                if opts['end_date'] is not None:
                    if(type(opts['end_date']) is datetime.date):
                        end_str = opts['end_date'].strftime('%Y-%m-%dT00:00:00.000Z')
                    else:
                        end_str = opts['end_date'].isoformat() + 'Z'

            if 'start_date' in opts:
                if(type(opts['start_date']) is datetime.date):
                    start_str = opts['start_date'].strftime('%Y-%m-%dT00:00:00.000Z')
                else:
                    start_str = opts['start_date'].isoformat() + 'Z'

            qString += ' AND endposition:[%s TO %s]'%(start_str, end_str)

        return qString

    def Search(self, **kwargs):
        """ Search for Sentinel-1 data in a particular region and a particular
           time period.

           ARGUMENTS:
            **kwargs: Additional keywords for search.  Typical keys include:
                    - start_date (datetime.date)
                    - end_date (datetime.date)
                    - region (list of tuples) A list of (lat,lon) pairs defining a region
                        of interest.

                Other keys can be any query arguments expected by the API.
                See the "Search Keywords" section of https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
                Examples include:
                    - "producttype" (e.g., 'SLC', 'GRD', 'OCN')
                    - "rows" Maximum number of results returned

          RETURNS:

        """
        qString = self._GetQueryString(kwargs)

        query = {'q':qString, 'rows':2, 'format':'json'}
        r = requests.get(self._url_search,auth=(self._user,self._pass),params=query)
        d = r.json()
        for name in d['feed']['entry']:
            print(name['title'])


if __name__=='__main__':

    hub = CopernicusHub('parnomd', getpass.getpass())
    hub.Search(type='SLC', end_date=datetime.datetime(year=2019,month=1,day=1))
