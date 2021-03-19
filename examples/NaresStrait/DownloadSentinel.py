"""

This example shows how to use the CRREL-SIRC rstools package to search for
Sentinel-1 imagery and download the files.

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
    poly = [(-64.25, 82.9), (-83.77, 78.37), (-64.87, 77.63), (-51.7, 82.78)]  # (lon, lat)

    # Search using the CopernicusHub API
    print("Performing Search...")
    matches = hub.Search(rows=100, # Maximum number of results returned
                         type='GRD',
                         sensoroperationalmode='EW',
                         polarisationmode='HH',
                         start_date=dt.datetime(year=2020,month=4,day=20),
                         end_date  =dt.datetime(year=2020,month=4,day=21),
                         region=poly)

    # List all of the results
    print('Details of search result: ')
    for match in matches:
        print('  Title: ', match['title'])
        for key, value in hub.ParseName(match['title']).items():
            print('  {}: {}'.format(key,value))
        print(' ')

    print('Total number of matches = ', len(matches))
    # Set the folder where we want to download the imagery
    data_folder = './sentinel-data'


    downloaded_files  = []

    for match in matches:

        if('GRDH' in match['title']):
            # Use glob to check to see if the file already exists
            existing_files = glob.glob(data_folder + '/' + match['title'] + '*.zip')

            # If the file exists, just return it's name
            if(len(existing_files)>0):
                print('File "',  match['title'], '" already exists.')
                downloaded_files.append(existing_files[0].split('/')[-1])

            # otherwise, download the file and return the name of the downloaded file
            else:
                files = hub.Download(data_folder, match)
                print('Downloaded ', files)
                downloaded_files.append(files[0])

    return downloaded_files

if __name__=='__main__':
    all_files = GetData()
