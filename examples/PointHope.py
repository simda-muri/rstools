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
import os

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
    existing_files = glob.glob(data_folder + '/' + matches[0]['title'] + '*.zip')
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

        Useful tutorials:
            - https://thegeoict.com/blog/2019/08/22/processing-sentinel-1-sar-images-using-snappy-snap-python-interface/
            - https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy/blob/master/s1_preprocessing.py
        ARGUMENTS:
            filename (string) : The name of the file downloaded in the GetData function.

    """

    import snappy

    from snappy import ProductIO, WKTReader
    from snappy import HashMap

    import gc
    from snappy import GPF

    ## UTM projection parameters
    proj = '''PROJCS["UTM Zone 4 / World Geodetic System 1984",GEOGCS["World Geodetic System 1984",DATUM["World Geodetic System 1984",SPHEROID["WGS 84", 6378137.0, 298.257223563, AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]],UNIT["degree", 0.017453292519943295],AXIS["Geodetic longitude", EAST],AXIS["Geodetic latitude", NORTH]],PROJECTION["Transverse_Mercator"],PARAMETER["central_meridian", -159.0],PARAMETER["latitude_of_origin", 0.0],PARAMETER["scale_factor", 0.9996],PARAMETER["false_easting", 500000.0],PARAMETER["false_northing", 0.0],UNIT["m", 1.0],AXIS["Easting", EAST],AXIS["Northing", NORTH]]'''

    # Make sure we're working with a zip file like we expect
    assert(filename.split('.')[-1]=='zip')
    data_folder = './example_data'

    # Check if this file has already been uncompressed
    extracted_name = data_folder + '/' + '.'.join(filename.split('.')[0:-1]) + '.SAFE'
    if(os.path.isdir(extracted_name)):
        print('File {} has already been extracted...'.format(filename))
    else:
        # First, extract the zip file
        print('Extracting {} ...'.format(filename))
        os.system('unzip -o ' + data_folder + '/' + filename + ' -d ' + data_folder)
        print('done')



    gc.enable()

    sentinel_1 = ProductIO.readProduct(extracted_name + "/manifest.safe")

    # polarization = 'VV'
    # parameters = HashMap()
    # parameters.put('outputSigmaBand', True)
    # parameters.put('outputGammaBand',False)
    # parameters.put('outputBetaBand',False)
    # parameters.put('sourceBands', 'Intensity_' + polarization)
    # parameters.put('selectedPolarisations', polarization)
    # parameters.put('outputImageScaleInDb', False)
    #
    # #calib = output + date + "_calibrate_" + polarization
    # target_0 = GPF.createProduct("Calibration", parameters, sentinel_1)

    wkt = "POLYGON((-167.3 68.5, -166.45 68.5, -166.45 68.1, -167.3 68.1, -167.3 68.5))"
    SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    geom = WKTReader().read(wkt)
    op = SubsetOp()
    op.setSourceProduct(sentinel_1)
    op.setCopyMetadata(True)

    sub_product = op.getTargetProduct()

    ProductIO.writeProduct(sub_product, 'result', 'GeoTIFF')


if __name__=='__main__':
    filename = GetData()
    ProcessData(filename)
