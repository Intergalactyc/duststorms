## NASA MODIS data
MODIS/Terra 10 km data (MOD04_L2): https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD04_L2

MODIS/Aqua 10 km data (MYD04_L2): https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MYD04_L2

### To run EarthData download scripts:
AWAITING at https://search.earthdata.nasa.gov/downloads/3563408866

Linux: You must first make the script an executable by running the line 'chmod 777 download.sh' from the command line. After that is complete, the file can be executed by typing './download.sh'.

Windows: The file can be executed within Windows by first installing a Unix-like command line utility such as Cygwin. After installing Cygwin (or a similar utility), run the line 'chmod 777 download.sh' from the utility's command line, and then execute by typing `./<filename>.sh`.

## GOES satellite data
GOES-13 operational during most of 2012-2014 (https://www.ssec.wisc.edu/datacenter/goes-archive/)

Search data at https://inventory.ssec.wisc.edu/inventory/?

Want: Channel 1 (visible), channels 4 & 6 (IR: BT(ch4)-BT(ch6) negative or near-zero for dust, positive for clouds)