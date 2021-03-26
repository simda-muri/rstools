"""
For reference, see
- http://step.esa.int/docs/tutorials/S1TBX%20SAR%20Basics%20Tutorial.pdf
- https://asf.alaska.edu/how-to/data-recipes/how-to-radiometrically-terrain-correct-rtc-sentinel-1-data-using-s1tbx-script/

"""
import glob

from rstools.processing import SentinelProcessor

data_folder = 'sentinel-data'
out_dir = data_folder+'/processed/'
gpt_exe = '/Applications/snap/bin/gpt'

# Get a list of the all the downloaded zip files
# 30D0 is a good look of the upper neck
# 7ADB is a good look at the main basin and south
# 50C1 is another good look at the main basin
zip_list =  glob.glob(data_folder + '/S1*50C1*.zip')

# Loop over all the images
for zip_file in zip_list:

    # Extract the name of the zip_file
    base_name = zip_file.split('/')[-1].replace('.zip','')

    proc = SentinelProcessor(zip_file, gpt_exe, out_dir)

    proc.ApplyOrbit()

    proc.RemoveThermalNoise('HH')
    proc.CleanTemp()

    proc.ApplyCalibration()
    proc.CleanTemp()

    proc.ApplyEllipsoidalCorrection()
    proc.CleanTemp()

    proc.Reproject('3413')
    proc.CleanTemp()

    proc.ConvertToDB()
    proc.CleanTemp()

    proc.Write('GeoTiff')
    proc.CleanTemp()
