"""
For reference, see
- http://step.esa.int/docs/tutorials/S1TBX%20SAR%20Basics%20Tutorial.pdf
- https://asf.alaska.edu/how-to/data-recipes/how-to-radiometrically-terrain-correct-rtc-sentinel-1-data-using-s1tbx-script/

"""
import glob
import os
import re
import shutil

data_folder = 'sentinel-data'
out_dir = data_folder+'/processed/'
gpt_exe = '/Applications/snap/bin/gpt'

tmp_dir =out_dir+'temp/'
proj = 'EPSG:4326'
def ApplyOrbit(input_name, output_name):
    """ Uses SNAP to apply the precise orbit file to a Sentinel-1 SAR file. """
    cmd = gpt_exe + ' Apply-Orbit-File -t ' + output_name
    cmd += ' -PcontinueOnFail=\"true\" -PorbitType=\'Sentinel Precise (Auto Download)\' '
    cmd += input_name
    os.system(cmd)
    return output_name+'.dim'

def ApplyCalibration(input_name, output_name):
    """ Uses SNAP to apply radiometric calibration. """
    cmd = gpt_exe + ' Calibration -PoutputBetaBand=true -PoutputSigmaBand=true '
    cmd += '-t ' + output_name
    cmd += ' -Ssource=' + input_name
    os.system(cmd)
    return output_name+'.dim'

def ConvertToDB(input_name, output_name):
    """ Converts to/from decibel scale. """
    cmd = gpt_exe + ' LinearToFromdB'
    cmd += ' -t ' + output_name
    cmd += ' -Ssource=' + input_name
    os.system(cmd)
    return output_name+'.dim'
#
# def ApplyTerrainFlattening(input_name, output_name):
#     """ Uses SNAP to apply terrain flattening. """
#     cmd = gpt_exe + ' Terrain-Flattening' # <- Specify the operation
#     cmd += ' -t '  + output_name # <- Specify the output name
#     cmd += ' -Ssource='  + input_name
#     cmd += ' -PdemName=\"SRTM 1Sec HGT\"'
#     os.system(cmd)
#     return output_name+'.dim'
#
# def ApplyTerrainCorrection(input_name, output_name):
#
#     cmd = gpt_exe + ' Terrain-Correction'
#     cmd += ' -t ' + output_name
#     cmd += ' -Ssource=' + input_name
#     cmd += ' -PsaveDEM=true -PsaveProjectedLocalIncidenceAngle=true'
#     cmd += ' -PpixelSpacingInMeter=50 -PmapProjection=EPSG:3413'
#     cmd += ' -PdemName=\"SRTM 1Sec HGT\"'
#     os.system(cmd)
#     return output_name+'.dim'

def Unzip(zip_file):
    """ Checks to see if the specified zip folder  has been uncompressed.  If not,
        this function unzips it.
    """
    assert (zip_file[-4:]=='.zip')
    unzipped_dir = zip_file[0:-4]+'.SAFE'

    if(not os.path.isdir(unzipped_dir)):
        res_folder = '/'.join(zip_file.split('/')[0:-1])
        os.system('unzip -o ' + zip_file + ' -d ' + res_folder)

    return unzipped_dir

def MakeGeoTiff(input_file, output_file, utm_info):
    """ Uses GDAL to convert the SNAP output into a geotiff. """

    # print(input_file,output_file)
    # input_dir = '/'.join(input_file.split('/')[0:-1])
    # output_dir = '/'.join(output_file.split('/')[0:-1])
    # input_name = input_file.split('/')[-1]
    # output_name = output_file.split('/')[-1]
    (zone, cm, hemi) = utm_info

    # os.chdir(input_dir)
    proj_str = ''
    if hemi == "S":
        proj_str = 'EPSG:327%02d ' % zone
    else:
        proj_str = 'EPSG:326%02d ' % zone

    cmd = 'gdal_translate -a_srs {} -of GTiff {} {}'.format(proj_str, input_file,output_file)
    os.system(cmd)
    # cmd = 'mv {} {}'.format(output_name, output_file)
    # os.system(cmd)

# Get the UTM zone, central meridian, and hemisphere
def getZone(inData):
    temp = inData.replace('.zip','.SAFE')
    if not os.path.isdir(temp):
        cmd = "unzip %s" % inData
        #print cmd
        os.system(cmd)
    back = os.getcwd()
    os.chdir(temp)
    os.chdir('annotation')

    paths = os.listdir(os.getcwd())
    for temp in paths:
        if os.path.isfile(temp):
            toread = temp
            break
    f = open(toread,'r')

    min_lon = 180
    max_lon = -180
    for line in f:
        m = re.search('<longitude>(.+?)</longitude>', line)
        if m:
            lon = float(m.group(1))
            if lon > max_lon:
                max_lon = lon
            if lon < min_lon:
                min_lon = lon
    f.close
    #print("Found max_lon of %s" % max_lon)
    #print("Found min_lon of %s" % min_lon)
    center_lon = (float(min_lon) + float(max_lon)) / 2.0
    #print "Found center_lon of %s" % center_lon
    zone = int(float(lon)+180)/6 + 1
    #print "Found UTM zone of %s" % zone
    central_meridian = (zone-1)*6-180+3
    #print "Found central meridian of %s" % central_meridian

    f = open(toread,'r')

    min_lat = 180
    max_lat = -180
    for line in f:
        m = re.search('<latitude>(.+?)</latitude>', line)
        if m:
            lat = float(m.group(1))
            if lat > max_lat:
                max_lat = lat
            if lat < min_lat:
                min_lat = lat
    f.close
    #print "Found max_lat of %s" % max_lat
    #print "Found min_lat of %s" % min_lat
    center_lat = (float(min_lat) + float(max_lat)) / 2.0
    #print "Found center_lat of %s" % center_lat
    if (center_lat < 0):
        hemi = "S";
    else:
        hemi = "N";
    #print "Found hemisphere of %s" % hemi

    os.chdir(back)
#    cmd = "rm -r %s" % inData.replace('.zip','.SAFE')
#    os.system(cmd)
    return (zone, central_meridian, hemi)

# Make the output directory if it doesn't exist
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Get a list of the all the downloaded zip files
# 30D0 is a good look of the upper neck
# 7ADB is a good look at the main basin and south
# 50C1 is another good look at the main basin
zip_list =  glob.glob(data_folder + '/S1*50C1*.zip')

# Loop over all the images
for zip_file in zip_list:

    # Extract the name of the zip_file
    base_name = zip_file.split('/')[-1].replace('.zip','')

    utm_info = getZone(zip_file)

    # Apply the precise orbit
    print('\n\n==================================')
    print('Applying Orbit File')
    print('    ', base_name)
    print('----------------------------------\n\n')
    ob_name = tmp_dir + base_name + '_OB'
    ob_data = ApplyOrbit(zip_file, ob_name)

    # Apply radiometric calibration
    print('\n\n==================================')
    print('Applying Calibration')
    print('    ', base_name)
    print('----------------------------------\n\n')
    rc_name = tmp_dir + base_name + '_CAL'
    rc_data = ApplyCalibration(ob_data, rc_name)

    # Clean up orbit file
    shutil.rmtree(ob_name+'.data',ignore_errors=True)
    os.remove(ob_name+'.dim')

    # Convert to decibel scale
    print('\n\n==================================')
    print('Converting to Decibels')
    print('    ', base_name)
    print('----------------------------------\n\n')
    db_name = tmp_dir + base_name + '_DB'
    db_data = ConvertToDB(rc_data, db_name)

    # Clean up calibration
    shutil.rmtree(rc_name+'.data',ignore_errors=True)
    os.remove(rc_name+'.dim')

    print('\n\n==================================')
    print('Writing GeoTiffs')
    print('    ', base_name)
    print('----------------------------------\n\n')
    img_files = glob.glob(db_data[0:-4] +  '.data/*.img')
    for img_file in img_files:
        img_name = img_file.split('/')[-1].split('.')[0]
        out_file = out_dir + base_name + '_CAL_DB_' + img_name + '.tiff'
        MakeGeoTiff(img_file, out_file, utm_info)

    # Clean up decibels
    shutil.rmtree(db_name+'.data',ignore_errors=True)
    os.remove(db_name+'.dim')
