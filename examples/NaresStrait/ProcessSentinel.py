"""
For reference, see
- http://step.esa.int/docs/tutorials/S1TBX%20SAR%20Basics%20Tutorial.pdf
- https://asf.alaska.edu/how-to/data-recipes/how-to-radiometrically-terrain-correct-rtc-sentinel-1-data-using-s1tbx-script/

"""
import glob

import pyroSAR.snap.auxil as sar #import parse_recipe, parse_node, gpt


data_folder = 'sentinel-data'
out_dir = data_folder+'/processed/'
gpt_exe = '/Applications/snap/bin/gpt'

# Get a list of the all the downloaded zip files
# 30D0 is a good look of the upper neck
# 7ADB is a good look at the main basin and south
# 50C1 is another good look at the main basin
files =  glob.glob(data_folder + '/S1*50C1*.zip')

# Loop over all the images
for zip_file in files[1:]:

    print('Processing ', zip_file,flush=True)

    steps = []

    workflow = sar.parse_recipe('blank')

    steps.append( sar.parse_node('Read') )
    steps[-1].parameters['file'] = zip_file
    steps[-1].parameters['formatName'] = 'SENTINEL-1'
    workflow.insert_node(steps[-1])

    steps.append( sar.parse_node('Apply-Orbit-File') )
    steps[-1].parameters['orbitType'] = 'Sentinel Precise (Auto Download)'
    workflow.insert_node(steps[-1], before=steps[-2].id)

    steps.append( sar.parse_node('ThermalNoiseRemoval') )
    steps[-1].parameters['selectedPolarisations'] = ['HH,HV']
    workflow.insert_node(steps[-1], before=steps[-2].id)

    # steps.append( parse_node('Remove-GRD-Border-Noise') )
    # steps[-1].parameters['selectedPolarisations'] = ['HH','HV']
    # workflow.insert_node(steps[-1], before=steps[-2].id)

    steps.append( sar.parse_node('Calibration') )
    steps[-1].parameters['outputSigmaBand'] = 'true'
    workflow.insert_node(steps[-1], before=steps[-2].id)

    # steps.append( sar.parse_node('Speckle-Filter') )
    # steps[-1].parameters['filter'] = 'Refined Lee'
    # workflow.insert_node(steps[-1], before=steps[-2].id)

    steps.append( sar.parse_node('Ellipsoid-Correction-GG') )
    workflow.insert_node(steps[-1], before=steps[-2].id)

    # # steps.append( sar.parse_node('Reproject') )
    # # steps[-1].parameters['crs'] = 'EPSG:3413'
    # # workflow.insert_node(steps[-1], before=steps[-2].id)

    steps.append( sar.parse_node('LinearToFromdB') )
    workflow.insert_node(steps[-1], before=steps[-2].id)

    steps.append( sar.parse_node('Write') )
    steps[-1].parameters['file'] = 'ProcessedSentinel/' + zip_file[0:-4].split('/')[-1] + '_PROCESSED'
    steps[-1].parameters['formatName'] = 'BEAM-DIMAP'
    workflow.insert_node(steps[-1], before=steps[-2].id)

    workflow.write('SarProcessing')

    grps = sar.groupbyWorkers('SarProcessing.xml', n=2)
    print(grps)
    sar.gpt('SarProcessing.xml', './results', groups=grps)#, outdir='./results')
