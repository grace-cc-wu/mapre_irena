##--------------------------------Preamble ----------------------------------

import arcpy
import numpy
import scipy.stats as stats
import math
import time
import os
import xlrd
import glob
import collections
start_time = time.time()
print start_time
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
from arcpy import env
from arcpy.sa import *
import arcpy.cartography as CA
arcpy.env.overwriteOutput = True

##---------------------Controls----------------------------------------------
technology = "wind" ##^^ input "wind" or "Ag" or "solarPV" or "solarCSP"
windThreshold = "250"
solarPVthreshold = "230"
solarCSPthreshold = "270"
Ag = "yes" # "yes" if specifying wind-ag, otherwise, "no"
buffered = "no" 
country = "angola"
countryAbv = "ao" ##^^ set country abbreviation here for purposes of file naming
dateAnalysis = "07302014" ##^^ this date will be used to create the output database
yourSpace = "A:\\" ##^^ This is the directory path before the IRENA folder structure
pathToRscripts = "A:\\IRENA\\PythonScripts\\"
spatialUnit = "zones"
##---------------------Local Parameters and workspace------------------------

# workspace for saving ouptuts. set for each technology
outputFolder = yourSpace + "IRENA\\OUTPUTS\\" + country + "\\" + dateAnalysis + "_" + countryAbv + "\\"
if not os.path.exists(outputFolder):
    print "outputFolder does not exist. Ensure you have selected the right date's resource potential feature class"

gdbName = dateAnalysis + "_" + countryAbv + ".gdb\\" ## ^^ Name of the fgdb to store outputs 
gdbNameForCreatingFGDB = dateAnalysis + "_" + countryAbv + ".gdb" ## ^^ here re-write the name of the file geodatabase
if not(os.path.exists(outputFolder + gdbName)): # Create new fgdb if one does not already exist
    print gdbName + " does not exist. Ensure you have selected the right date's resource potential feature class" 

outputFGDB = outputFolder + gdbName # sets workspace as your fgdb 
env.scratchWorkspace = outputFGDB # sets scratchworkspace to your output workspace 
env.workspace = outputFGDB # sets environment workspace to your output workspace

# set input paths:
defaultInputWorkspace = yourSpace + "IRENA\\INPUTS\\" ##^^ enter the path to your DEFAULT INPUT path
countryWorkspace = defaultInputWorkspace + "Countries\\" + country + "\\" + countryAbv + ".gdb\\" ##^^ enter the path to your COUNTRY INPUT fgdb here (should be countryName.fgdb)
countryBounds = countryWorkspace + countryAbv + "_GADM_countryBounds" ##^^ enter the path to your COUNTRY boundary shapefile


templateRaster = "A:\\IRENA\\INPUTS\\" + "technoeconomic.gdb\\mergedDEM_GADM_500"
wgsTemplate = "A:\\IRENA\RawData\\wwf_official_terrestrialEcoregionsWorld\official\\wwf_terr_ecos.shp"
UTMtemplate = 'A:\\IRENA\\INPUTS\\Countries\\tanzania\\infrastructure\\solarSites_36S.shp'

spatial_ref_africa = arcpy.Describe(templateRaster).spatialReference
spatial_ref_WGS84 = arcpy.Describe(wgsTemplate).spatialReference
spatial_ref_UTM = arcpy.Describe(UTMtemplate).spatialReference

# set environments for raster analyses
arcpy.env.snapRaster = templateRaster
arcpy.env.extent = countryBounds
arcpy.env.mask = countryBounds
arcpy.env.cellSize = templateRaster

if buffered == "yes":
    solarPVzones = countryAbv +  "_solarPV_globalMapV2_solarExclusions_threshold" + solarPVthreshold + "_buffered_" + spatialUnit 
    solarCSPzones = countryAbv +  "_solarCSP_globalMapV2_solarExclusions_threshold" + solarCSPthreshold + "_buffered_" + spatialUnit 
    if Ag == "yes":
        windZones = countryAbv +  "_wind_globalMapV2_windExclusionsAg_threshold" + windThreshold+ "_buffered_" + spatialUnit 
    else:
        windZones = countryAbv +  "_wind_globalMapV2_windExclusions_threshold" + windThreshold + "_buffered_" + spatialUnit 
if buffered == "no":
    solarPVzones = countryAbv +  "_solarPV_globalMapV2_solarExclusions_threshold" + solarPVthreshold + "_" + spatialUnit 
    solarCSPzones = countryAbv +  "_solarCSP_globalMapV2_solarExclusions_threshold" + solarCSPthreshold + "_" + spatialUnit 
    if Ag == "yes":
        windZones = countryAbv +  "_wind_globalMapV2_windExclusionsAg_threshold" + windThreshold+ "_" + spatialUnit 
    else:
        windZones = countryAbv +  "_wind_globalMapV2_windExclusions_threshold" + windThreshold + "_" + spatialUnit 
print windZones


if technology == "solarPV":
    zone_orig = outputFGDB + solarPVzones
    zoneFile = arcpy.CopyFeatures_management(zone_orig, "in_memory/zones")
    zoneFileForMap = arcpy.CopyFeatures_management(zone_orig +"forMap", "in_memory/zonesForMap")
    technologyNameForDistance = "PV"

if technology == "solarCSP":
    zone_orig = outputFGDB + solarCSPzones
    zoneFile = arcpy.CopyFeatures_management(zone_orig, "in_memory/zones") 
    zoneFileForMap = arcpy.CopyFeatures_management(zone_orig +"forMap", "in_memory/zonesForMap")
    technologyNameForDistance = "CSP"

if technology == "wind":
    zone_orig = outputFGDB + windZones
    zoneFile = arcpy.CopyFeatures_management(zone_orig, "in_memory/zones")
    zoneFileForMap = arcpy.CopyFeatures_management(zone_orig +"forMap", "in_memory/zonesForMap")
    technologyNameForDistance = "wind"

print "Joining capacity value calculations for :" + zone_orig

################
## IMPORT CSV ##
################

csvFolder = "A:\\IRENA\\INPUTS\\capacityValue\\"
csvFile = glob.glob(csvFolder + countryAbv + "*")[0]


'''
##################
## GEOPROCESSES ##
##################
'''

env.workspace = csvFolder

x_coords = "longitude"
y_coords = "latitude"
z_coords = ""
out_layer = countryAbv + "_capVal"

# Set the spatial reference
spRef = spatial_ref_WGS84

# Make the XY event layer...
arcpy.MakeXYEventLayer_management(csvFile, x_coords, y_coords, out_layer, spRef, z_coords)
print "made XY event layer"

# Print the total rows
print arcpy.GetCount_management(out_layer)

# # Save to a layer file
# arcpy.SaveToLayerFile_management(out_Layer, defaultInputWorkspace + "Countries\\" + country + "\\" + countryAbv +"_capacityValueLocations")

## save layer to a feature class:
windLocations = arcpy.CopyFeatures_management(out_layer, countryWorkspace + countryAbv +"_capacityValueLocations")

## project 
windLocations_proj = arcpy.Project_management(windLocations, windLocations[0] + "_proj", spatial_ref_africa)

## get centroids of zones:
centroids = arcpy.FeatureToPoint_management(zoneFile, "in_memory/centroids", "CENTROID")

arcpy.Near_analysis(centroids, windLocations_proj[0], "", "NO_LOCATION", "NO_ANGLE")

# Add new field for distance: 
arcpy.AddField_management(centroids, "distance_nearest_3TierWindLocation_km", "DOUBLE")
arcpy.CalculateField_management(centroids, "distance_nearest_3TierWindLocation_km", "int(!NEAR_DIST!/1000)", "PYTHON_9.3")
arcpy.DeleteField_management(centroids, "NEAR_DIST")
print "Distance calculations are complete"

## join fields from windlocations to centroid:
arcpy.JoinField_management(centroids, "NEAR_FID", windLocations_proj[0], "OBJECTID", ["siteName", "capacityValueRatio_actual_peakHrs",\
							"capacityValueRatio_specified_peakHrs", \
							"capacityValueRatio_specified_peakHrs_multYear"])

## join fields from centroid to zoneFile:
arcpy.JoinField_management(zoneFile, "OBJECTID", centroids, "OBJECTID", ["siteName","distance_nearest_3TierWindLocation_km",\
							"capacityValueRatio_actual_peakHrs",\
							"capacityValueRatio_specified_peakHrs", \
							"capacityValueRatio_specified_peakHrs_multYear"])

fieldNameDict = collections.OrderedDict()
fieldNameDict["capacityValueRatio_actual_peakHrs"] = "capacityValueRatio_10percentPeakHours"
fieldNameDict["capacityValueRatio_specified_peakHrs"] = "capacityValueRatio_chosen3peakHours"
fieldNameDict["capacityValueRatio_specified_peakHrs_multYear"] = "capacityValueRatio_chosen3peakHours_multiyear"

for each in fieldNameDict:
	arcpy.AddField_management(zoneFile, fieldNameDict[each], "DOUBLE")
	arcpy.CalculateField_management(zoneFile, fieldNameDict[each], "round(!" + each + "!, 2)", "PYTHON_9.3")
	arcpy.DeleteField_management(zoneFile, each)

# ## calculate nearest point location
# arcpy.Near_analysis(zoneFile, windLocations_proj[0], "", "NO_LOCATION", "NO_ANGLE")

# # Add new field for distance: 
# arcpy.AddField_management(zoneFile, "distance_nearest_3TierWindLocation_km", "DOUBLE")
# arcpy.CalculateField_management(zoneFile, "distance_nearest_3TierWindLocation_km", "!NEAR_DIST!/1000", "PYTHON_9.3")
# arcpy.DeleteField_management(zoneFile, "NEAR_DIST")
# print "Distance calculations are complete"

# ## join fields from point location to zoneFile:
# arcpy.JoinField_management(zoneFile, "NEAR_FID", windLocations_proj[0], "OBJECTID", ["siteName",\
# 							"capacityValueRatio_actual_peakHrs",\
# 							"capacityValueRatio_specified_peakHrs", \
# 							"capacityValueRatio_specified_peakHrs_multYear"])

# arcpy.DeleteField_management(zoneFile, "NEAR_FID")

## join fields from point location to zonesForMap:
arcpy.JoinField_management(zoneFileForMap, "zone_identification", zoneFile, "zoneIdentification", ["distance_nearest_3TierWindLocation_km", \
							"capacityValueRatio_10percentPeakHours",\
							"capacityValueRatio_chosen3peakHours", \
							"capacityValueRatio_chosen3peakHours_multiyear"])


arcpy.CopyFeatures_management(zoneFile, zone_orig + "_capVal")
arcpy.CopyFeatures_management(zoneFileForMap, zone_orig +"forMap" + "_capVal")

elapsed_time = time.time() - start_time
print str(elapsed_time/(60*60)) + " hours"
