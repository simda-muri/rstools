"""
Tools for downloading Sentinel-1 SAR data using the [Copernicus Open Access API.](https://scihub.copernicus.eu/twiki/do/view/SciHubWebPortal/APIHubDescription)

"""

import numbers
import requests
import datetime
import time
from tqdm import tqdm
import os
import re


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

    def __init__(self, username, password, platform='Sentinel-1'):
        self._user = username
        self._pass = password
        self._url_search = 'https://scihub.copernicus.eu/dhus/search'
        self._url_data = 'https://scihub.copernicus.eu/dhus/odata/v1'
        self._platform  = platform


    def ParseName(name):
        """
        Parses information from a Sentinel filename (e.g., S1A_IW_GRDH_1SDV_20200629T174145_20200629T174210_033235_03D9B9_D763)
        Returns a dictionary with information.  Currently only supports Sentinel-1 names.

        See https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar/naming-conventions
        """

        if(name[1]!='1'):
            raise RuntimeError('ParseName function currently only supports Sentinel-1 filenames.')

        parts = re.split('_+',name.split('.')[0])

        out = dict()
        out['ID'] = parts[0] # Mission ID
        out['BeamMode'] = parts[1]
        out['Product'] = parts[2][0:3]
        if(out['Product']=='GRD'):
            out['Resolution'] = parts[2][-1] # Resolution class

        out['Level'] = parts[3][0] # Processing level
        out['Polarization'] = parts[3][-2:] # Polarization, either SH, SV, DH, or DV

        out['StartTime'] = datetime.datetime.strptime(parts[4], '%Y%m%dT%H%M%S')
        out['EndTime'] = datetime.datetime.strptime(parts[5], '%Y%m%dT%H%M%S')
        out['AbsOrbit'] = int(parts[6])

        # Figure out the relative orbit number (see https://forum.step.esa.int/t/sentinel-1-relative-orbit-from-filename/7042/2)
        if(out['ID']=='S1A'):
            out['RelOrbit'] = 1+ (out['AbsOrbit']-73) % 175
        elif(out['ID']=='S1B'):
            out['RelOrbit'] = 1+(out['AbsOrbit']-27) % 175
        return out

    def Search(self, rows=10, sort_dir='desc', **kwargs):
        """ Search for Sentinel-1 data in a particular region and a particular
           time period.

           ARGUMENTS:
            rows (int, optional): Maximum number of results to return
            sort_dir (string,optional): How to sort the results.  Either asc or desc

            **kwargs: Additional keywords for search.  Typical keys include:
                    - start_date (datetime.date)
                    - end_date (datetime.date)
                    - region (list of tuples) A list of (lon,lat) pairs defining
                        a polygonal region of interest.  Sentinel images with
                        footprints that intersect this polygon are returned.
                        If only a single point is provided, then images with
                        footprints containing that point are returned.

                Other keys can be any query arguments expected by the API.
                See the "Search Keywords" section of https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
                Examples include:
                    - "producttype" (e.g., 'SLC', 'GRD', 'OCN')
                    - "collection"
                    - "filename"
                    - "orbitnumber"
                    - "relativeorbitnumber" (used for interferometric applications)
                    - "polarisationmode" (e.g., 'HH', 'VV', 'HV', 'VH', 'HH HV', 'VV VH')

          RETURNS:

        """
        max_tries = 5

        assert sort_dir in ['asc','desc']
        qString = self._GetQueryString(kwargs)

        query = {'q':qString, 'rows':rows, 'orderby':'beginposition '+sort_dir, 'format':'json'}

        for num_tries in range(max_tries):
            r = requests.get(self._url_search,auth=(self._user,self._pass),params=query)
            if(r.status_code==200):
                break
            elif(r.status_code==429):
                print('In Search Attempt {}:\n  Received "Too Many Attempts" from API.  Waiting 2s and trying again'.format(num_tries))
                time.sleep(2)
            else:
                with open('api_error.html','wb') as f:
                    f.write(r.content)
                raise RuntimeError("Received error code {} from API.".format(r.status_code))

        d = r.json()

        # Do some error checking
        if 'feed' not in d:
            raise RuntimeError('Something went really wrong and I cannot parse the API response.')
        if 'error' in d['feed'].keys():
            raise RuntimeError("Received error from code {} API:\n  {}".format(d['feed']['error']['code'], d['feed']['error']['message']))

        # Extract the available imagery
        if('entry' not in d['feed']):
            return []
        else:
            return d['feed']['entry']


    def Download(self, folder, search_result):
        """ Downloads one or more results from the search.

            ARGUMENTS:
                folder (string) : Path to folder where downloaded files should be placed.
                search_result (string, dict, list of strings, list of dicts) : One or more
                    outputs from the Search function.  If a string or list of strings, the
                    strings must be URLs to the copernicus open data API, e.g., https://scihub.copernicus.eu/dhus/odata/v1/Products('2b7dfd40-a838-423d-8c2e-d2daa7c0bc09')/$value
                    If dict or list of dicts, the search_result argument must be of the
                    form returned by the Search function.  i.e., there must a
                    list of urls stored under the 'link' key in the dictionary.
                    The download URL is search_result[i]['link'][0]['href'].

            RETURNS:
                A list of strings containing the filenames of all the downloaded files.

        """

        # Get all of the urls we need to download
        urls=None
        if(isinstance(search_result, list)):
            if(isinstance(search_result[0],str)):
                urls = search_result
            else:
                urls = [res['link'][0]['href'] for res in search_result]
        else:
            if(isinstance(search_result,str)):
                urls = [search_result]
            else:
                urls = [search_result['link'][0]['href']]

        filenames = []
        for url in urls:
            res = self._download_from_url(folder,url)
            if(res is not None):
                filenames.append( res )

        return filenames


    def _download_from_url(self,folder, url):
        """
        Downloads the sentinel zip file from a url to a folder.
        """


        r = requests.get(url, stream=True, auth=(self._user,self._pass))
        if('content-disposition' not in r.headers):
            msg = ''
            if('<message xml:lang="en">' in str(r.content)):
                msg = str(r.content).split('<message xml:lang="en">')[1].split('</message>')[0]

            raise RuntimeError('Failed to download file.  This is most likely because user offline quota has been exceeded.  Wait an hour and try again.\n\n'+msg )

        filename = r.headers['content-disposition'].split('=')[1][1:-1]


        total_size_in_bytes= int(r.headers.get('content-length', 0))
        print('Downloading {}'.format(filename))

        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

        with open(folder+'/'+filename + '.part', 'wb') as file:
            for data in r.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong and only part of the file was downloaded.")
        else:
            os.rename(folder+'/'+filename + '.part', folder+'/'+filename)

        print(' ')

        return filename


    def _GetQueryString(self, opts):
        """ Processes optional arguments passed to the "Search" function to
            construct the query string required by the copernicus API.
        """
        qString = 'platformname:'+self._platform

        # Process the optioons into the query string
        if 'type' in opts:
            typestr = opts['type']
            if(self._platform=='Sentinel-1'):
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
                        end_str = opts['end_date'].isoformat() + '0Z'

            if 'start_date' in opts:
                if(type(opts['start_date']) is datetime.date):
                    start_str = opts['start_date'].strftime('%Y-%m-%dT00:00:00.000Z')
                else:
                    start_str = opts['start_date'].isoformat() + '0Z'

            qString += ' AND endposition:[%s TO %s]'%(start_str, end_str)

        # If a ROI is provided...
        if 'region' in opts:

            qString += ' AND footprint:"intersects('

            # Check if a polygon is defined or just a point
            if isinstance(opts['region'][0], numbers.Number):
                qString += '%0.4f %0.4f'%(opts['region'][0], opts['region'][1])

            # Otherwise it's a list of points defining a polygon...
            else:
                pts = opts['region']
                # Make sure the last point is the same as the first
                if((pts[-1][0] != pts[0][0]) or (pts[-1][1] != pts[0][1])):
                    pts.append(pts[0])

                qString += 'POLYGON(('
                qString += '%0.4f %0.4f'%(pts[0][0],pts[0][1])
                for pair in pts[1:]:
                    qString += ',%0.4f %0.4f'%(pair[0],pair[1])
                qString += '))'

            qString += ')"' # <- end of intersects(  string

        # Add all the other possible keys
        for key in opts.keys():
            if(key not in ['region', 'type', 'start_date', 'end_date']):
                qString += ' AND ' + key + ':' + opts[key]

        return qString


if __name__=='__main__':
    import getpass

    hub = CopernicusHub('parnomd', getpass.getpass())
    # print('No filters:')
    # hub.Search()
    #
    # print('SLC Filter:')
    # hub.Search(type='SLC')
    #
    # print('SLC and End Date filter:')
    # hub.Search(sort_dir='desc', type='SLC', end_date=datetime.datetime(year=2019,month=1,day=1))
    #
    # print('GRD and Start Date filter:')
    # hub.Search(type='GRD', start_date=datetime.datetime(year=2021,month=1,day=15))

    #######################################################
    print('GRD, Start Date, and point filter:')
    pt = (-148.8, 72.7) # (lon, lat)
    matches = hub.Search(type='GRD', start_date=datetime.datetime(year=2020,month=1,day=15), region=pt)

    for match in matches:
        print(match['title'])

    #######################################################
    print('GRD, Start Date, and polygon filter:')
    poly = [(-167.3, 68.5), (-166.45, 68.5), (-166.45, 68.1), (-167.3, 68.1)]  # (lon, lat)
    matches = hub.Search(type='GRD', start_date=datetime.datetime(year=2020,month=1,day=15), region=poly)

    for match in matches:
        print(match['title'])

    #######################################################
    print ("Downloading....")
    hub.Download('.', matches)
    hub.Download('.',matches[0])
    hub.Download('.',matches[0]['link'][0]['href'])
