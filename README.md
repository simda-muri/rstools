## Goal:
Provide a collection of python tools for downloading and processing SAR data for use in sea ice applications.

## Installation:

This package is built in python and relies heavily on the Snap tool for processing Sentinel data.  It also uses GDAL and rasterio for other geographic operations.

#### Step 1: Install SNAP
1. Download the installer from the [SNAP website](http://step.esa.int/main/download/snap-download/)
2. Figure out the full path to your favorite python executable.  In the terminal, run
```bash
which python
```
3. Run the SNAP installer.  

#### Step 2: Install Python Packages
```bash
conda install -c conda-forge gdal rasterio
```
## Examples:
See examples folder.
