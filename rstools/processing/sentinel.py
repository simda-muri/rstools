import os
import shutil

class SentinelProcessor:
    """ Uses the `gpt` tool distributed with SNAP to process Sentinel-1 data.
    """

    def __init__(self,
                 input_file,
                 gpt_path='/Applications/snap/bin/gpt',
                 out_dir=None):

        self.input_file = input_file
        self.base_name = input_file.split('/')[-1].split('.')[0]

        if(out_dir==None):
            out_dir = './processed/'

        # Create the output  directory if it doesn't exist
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        self.out_dir = out_dir

        if(self.out_dir[-1]!='/'):
            self.out_dir += '/'

        # Create a temporary working directory in the output directory
        self.tmp_dir = out_dir + "temp/"
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        # Set the GPT path and test to make sure it works
        self.gpt_exe = gpt_path

        # Keep a list of all previous output files that haven't been removed
        self.previous_outputs=[]

        # This is the most recent output produced by SNAP
        self.newest_output=None

    def CleanTemp(self):
        """ Removes previously generated intermediate files that are not necessary
            for subsequent operations.
        """
        for base_name in self.previous_outputs:
            print('Cleaning up "', base_name, '"')
            shutil.rmtree(base_name+'.data',ignore_errors=True)
            os.remove(base_name+'.dim')

        self.previous_outputs=[]


    def _PrintHeader(self,step_name):

        print('\n\n=================================')
        print(step_name)
        print('    ', self.base_name)
        print('---------------------------------\n\n')


    def _UpdateHistory(self, output_name):
        """ Updates the list of intermediate results so that we can clean them
            up later.
        """

        if(self.newest_output is not None):
            self.previous_outputs.append(self.newest_output)
        self.newest_output = output_name

    def _GetOutputName(self, type_str, temp=True):
        """
        Constructs the name of the next output from GPT using the current name
        and a short (e.g., 2 character) string describing the operation.
        """
        if(temp):
            return self.tmp_dir + self.base_name + '_' + type_str
        else:
            return self.out_dir + self.base_name + '_' + type_str

    def _GetInputName(self):

        # If this is the first step...
        if(self.newest_output is None):
            return self.input_file
        else:
            return self.newest_output+'.dim'

    def ApplyOrbit(self):
        """ Uses SNAP to apply the precise orbit file to a Sentinel-1 SAR file. """

        self._PrintHeader('Applying Orbit File')

        input_name = self._GetInputName()
        output_name = self._GetOutputName('OB')

        cmd = self.gpt_exe + ' Apply-Orbit-File -t ' + output_name
        cmd += ' -PcontinueOnFail=\"true\" -PorbitType=\'Sentinel Precise (Auto Download)\' '
        cmd += input_name
        os.system(cmd)

        self._UpdateHistory(output_name)

    def ApplyCalibration(self):
        """ Uses SNAP to apply radiometric calibration. """

        self._PrintHeader('Performing Radiometric Calibration')

        input_name = self._GetInputName()
        output_name = self._GetOutputName('CAL')

        cmd = self.gpt_exe + ' Calibration -PoutputBetaBand=false -PoutputSigmaBand=true '
        cmd += '-t ' + output_name
        cmd += ' -Ssource=' + input_name
        os.system(cmd)

        self._UpdateHistory(output_name)

    def ConvertToDB(self):
        """ Converts to/from decibel scale. """

        self._PrintHeader('Converting to Decibel Scale')

        input_name = self._GetInputName()
        output_name = self._GetOutputName('DB')

        cmd = self.gpt_exe + ' LinearToFromdB'
        cmd += ' -t ' + output_name
        cmd += ' -Ssource=' + input_name
        os.system(cmd)

        self._UpdateHistory(output_name)

    def RemoveThermalNoise(self,polarization=None):
        """ Removes thermal noise.  If polarization is None, all polarizations
            are processed.  Otherwise, only a subset (e.g. HH) is processed.

            The polarization argument should be a string readable by GPT that is
            passed to the `-PselectedPolarisations` option of the `gpt ThermalNoiseRemoval`
            command.
        """

        self._PrintHeader('Removing Thermal Noise')

        input_name = self._GetInputName()
        output_name = self._GetOutputName('TN')

        cmd = self.gpt_exe + ' ThermalNoiseRemoval'
        if(polarization is not None):
            cmd += ' -PselectedPolarisations=' + polarization
        cmd += ' -t ' + output_name
        cmd += ' -SsourceProduct=' + input_name
        os.system(cmd)

        self._UpdateHistory(output_name)


    def ApplyEllipsoidalCorrection(self):
        """ Uses SNAP to orthorectify the image. """

        self._PrintHeader('Applying Ellipsoidal Correction (Orthorectifying)')

        input_name = self._GetInputName()
        output_name = self._GetOutputName('GEO')

        cmd = self.gpt_exe + ' Ellipsoid-Correction-GG'
        cmd += ' -t ' + output_name
        cmd += ' -Ssource=' + input_name
        os.system(cmd)

        self._UpdateHistory(output_name)

    def Reproject(self,epsg='3413'):
        """ Reprojects to a CRS defined by an epsg.
        """
        self._PrintHeader('Reprojecting to EPSG:{}'.format(epsg))

        input_name = self._GetInputName()
        output_name = self._GetOutputName('PROJ')

        cmd = self.gpt_exe + ' Reproject -Pcrs=EPSG:%s'%epsg
        cmd += ' -t ' + output_name
        cmd += ' -Ssource=' + input_name
        os.system(cmd)

        self._UpdateHistory(output_name)


    def Write(self,file_format='GeoTiff'):
        """ Writes an output file using the most recent BEAM-DIMAP file created
            by `gpt`.

            ARGUMENTS:
                file_format (str) : The file format to output.  Examples include GeoTiff or BEAM-DIMAP.
        """
        self._PrintHeader('Writing output to {} file'.format(file_format))

        input_name = self._GetInputName()
        output_name = self._GetOutputName('Processed',False)

        cmd = self.gpt_exe + ' Write -PformatName={}'.format(file_format)
        cmd += ' -Pfile=' + output_name
        cmd += ' -Ssource=' + input_name

        os.system(cmd)

        self._UpdateHistory(output_name)
