"""

This example shows how to use the rstools package to search for
Sentinel-1 imagery and download the files.  It is also possible to process
the data using the rstools interface to SNAP.   See NaresStrait "ProcessSentinel.py"
example for details.

NOTE: Currently, this script will search for 2 matching results from CopernicusHub
      but will only download 1.

NOTE: This script will prompt you for a copernicus username and password.  This
      is the same information used to log in to Copernicus SciHub at
      https://scihub.copernicus.eu/dhus/#/home

"""

from rstools.download import CopernicusHub

import getpass
import datetime as dt
import glob
import os

def GetData():
    """ Uses the rstools module to search for and download Sentinel-1 imagery
        from the Copernicus API.

        RETURNS:
            A list of the downloaded zip files.
    """

    # Set up the interface with CopernicusHub
    print('Enter login information for Copernicus SciHub:')
    hub = CopernicusHub(input('  Copernicus Username: '),
                        getpass.getpass('  Copernicus Password: '),
                        platform='Sentinel-1')

    # Define a polygon for the ROI.  Images that intersect this poly will be returned
    poly = [(-167.3, 68.5), (-166.45, 68.5), (-166.45, 68.1), (-167.3, 68.1)]  # (lon, lat)

    # Search using the CopernicusHub API
    matches = hub.Search(rows=2, # Maximum number of results returned
                         type='GRD',
                         polarisationmode='VV',
                         start_date=dt.datetime(year=2020,month=6,day=1),
                         end_date  =dt.datetime(year=2020,month=6,day=30),
                         region=poly)

    # List all of the results
    print('Details of search result: ')
    for match in matches:
        print('  Title: ', match['title'])
        for key, value in hub.ParseName(match['title']).items():
            print('  {}: {}'.format(key,value))
        print(' ')

    # Set the folder where we want to download the imagery
    data_folder = './sentinel-data'

    # If the folder doesn't exist, create it
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # Use glob to check to see if the file already exists
    existing_files = glob.glob(data_folder + '/' + matches[0]['title'] + '*.zip')
    print('Existing files: ', existing_files)

    # If the file exists, just return it's name
    if(len(existing_files)>0):
        print('File already exists.')
        return existing_files[0].split('/')[-1]

    # otherwise, download the file and return the name of the downloaded file
    else:
        files = hub.Download(data_folder, matches[0])
        print('Downloaded ', files)
        return files[0]


if __name__=='__main__':
    filename = GetData()
