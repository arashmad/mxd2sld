# mxd_2_sld

**What Is this?**

This is a python script that let us generate standard and proper SLDs from each layer listed in ESRI ArcGIS map document `.mxd` file.

This process is done automatically, fast and suite.

You can track the process by checking `log.log` file located in the root of project to make sure if all layers in `.mxd` have been converted to SLD or not.

> !IMPORTANT This script is extending now because there are some complex styles defined in ArcMap that we are limited to convert them to SLD format.

**How does it work?**

There are some simple steps before running the scrip:

*(01) converting .mxd to .wrm format*

As the `.mxd` doesn't provide complete information about styles' properties like color, font and label, this script uses `.msd` format. Therefore we need to convert `.mxd` to `.msd` file format. To do so, follow these steps:
1. Make sure that all styled layers listed in `.mxd` file have been already linked to their data source (shapefile,feature class,...) and date is being represting in map layout. It's necessary because even if one of the layers has the **RED EXCLAMATION MARK** in the table of content, you are going to face ERROR during generating `.msd` file.
2. Run this python script in ArcMap python console to get `.msd` file
```python
import arcpy
mxd_name = '/path/to/mxd/file/<mxd_name>.mxd'
mxd_file = arcpy.mapping.MapDocument(mxd_name)
arcpy.mapping.ConvertToMSD(mxd_file, 'wrm')
```

*(02) Run the script*

Move output `.msd` file into `/root/msd`. If this directory doesn't exist, create it manually. Now run the `main.py` file to start generation process.

**Where can I find SLDs?**

After finishing the whole process, go to `/root` and you will see a directory named same as `.msd` file and illustrated by date and time.
```
<msd_file_name> ("%Y.%m.%d %H.%M.%S")
```
This contains two sub-directories; one for SLDs and one for images are being used as point symbol marker.