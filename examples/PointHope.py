"""

This example shows how to use the CRREL-SIRC rstools package to search for
Sentinel-1 imagery, download the files, and process them with the ESA snappy
python package.

The snappy processing is based on this example:
http://remote-sensing.org/preprocessing-of-sentinel-1-sar-data-via-snappy-python-module/

"""

from rstools.download import CopernicusHub

import getpass
import datetime as dt
import glob
import zipfile

def GetData():
    """ Uses the rstools module to search for and download Sentinel-1 imagery
        from the Copernicus API.

        RETURNS:
            A list of the downloaded zip files.
    """

    # Set up the interface with CopernicusHub
    hub = CopernicusHub('parnomd', getpass.getpass())

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
    print('  Title: ', matches[0]['title'])
    for key, value in hub.ParseName(matches[0]['title']).items():
        print('  {}: {}'.format(key,value))
    print(' ')

    # Set the folder where we want to download the imagery
    data_folder = './example_data'

    # Use glob to check to see if the file already exists
    existing_files = glob.glob(data_folder + '/' + matches[0]['title'] + '*')
    print(existing_files)

    # If the file exists, just return it's name
    if(len(existing_files)>0):
        print('File already exists.')
        return existing_files[0].split('/')[-1]

    # otherwise, download the file and return the name of the downloaded file
    else:
        files = hub.Download(data_folder, matches[0])
        print('Downloaded ', files)
        return files[0]


def ProcessData(filename):
    """ Uses snappy to preprocess the Sentinel-1 image.

        Based on http://remote-sensing.org/preprocessing-of-sentinel-1-sar-data-via-snappy-python-module/

        ARGUMENTS:
            filename (string) : The name of the file downloaded in the GetData function.

    """

    import snappy

    from snappy import ProductIO
    from snappy import HashMap

    import os, gc
    from snappy import GPF

    # Make sure we're working with a zip file like we expect
    assert(filename.split('.')[-1]=='zip')
    data_folder = './example_data'

    # First, extract the zip file
    with zipfile.ZipFile(data_folder + '/' + filename,"r") as zip_ref:
        zip_ref.extractall(data_folder)

if __name__=='__main__':
    filename = GetData()
    ProcessData(filename)
