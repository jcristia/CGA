#!/usr/bin/env python
"""Calculates amount of 'Conservation Priorities' currently protected by existing conservation areas in the North Shelf Bioregion"""

## Built in modules ##

import os, sys, csv, re

## Third party modules ##

import arcpy

## Authorship Information ##

__author__ = "Eric Pledger"
__email__ = "epledger@sfu.ca"
__status__ = "Prototype"

#############################################
### About subregionally clipped CP layers ###
#############################################

# This script will also report out on CPs based on the subregions in which
# they occur. A CP polygon layer that has been clipped by a subregion should
# have its feature datasetname be suffixed by any of the following depending
# on which subregion polygon it has been clipped by:
#
#       '_CC'   => Central Coast
#       '_NC'   => North Coast
#       '_HG'   => Haida Gwaii
#       '_NCVI' => North Coast Vancouver Island
#
# For example a CP feature class for tufted tuffin colonies clipped by the
# Haida Gwaii bioregion should be named:
#
#       mpatt_eco_birds_tuftedpuffin_colonies_seasketch_HG
#

#################################
### Configure these variables ###
#################################

### print_status & detailed_status ###
#
# If True various messages on the status of the script will be printed to the standard output
# while it is processing. Nothing will be printed to standard output if this is disabled.
#
# However, if an error occurs or exception is thrown that will still go to stderr. 
#
##

print_status = True
detailed_status = True

### source_mxd ###
#
# Path as string pointing to the mxd containing all of the MPAT layers to be used in the analysis
#
##

source_mxd = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\spatial\CP_HU_MPA_Layers.mxd'

### scaling_attribute & scaling_attribute_file ###
#
# Defines which attributes to use (if necessary) for scaling a layers area based on importance.
# If all layers have one consistent attribute name then set scaling_attribute. If layers have
# varying attribute names then set scaling_attribute_file. You must not set both.
#
# scaling_attribute should be the name of a scaling attribute used by every relevant layer as a
# string. If a layer does not have that attribute present it is assumed that no scaling is
# necessary. If using scaling_attribute_file then set this value to None
#
# scaling_attribute_file should be the path to a CSV file containing two columns. The first
# should be the feature class name or the name of the shapefile without the file extension and
# the second column should be the corresponding scaling attribute. If using scaling_attribute
# (i.e. all relevent layers have one name for scaling layer) then set this value to None.
#
# The scaling attribute used by a layer should be of a numeric data type. If both
# scaling_attribute and scaling_attribute_file are None then it is assumed that no scaling
# should occur.
#
##

scaling_attribute = None   # previously: 'RI'

scaling_attribute_file = None

### working_gdb_folder ###
#
# The path to a folder where temporary files are to be stored. Creates a new geodatabase with
# (hopefully) a unique name. The script deletes the database at the end but if an error is
# is thrown then one might linger. I would suggest cleaning out that folder every once in a
# while. 
#
##

working_gdb_folder = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\spatial\working_TEMP'

### sr_code ###
#
# The wkid for the spatial reference that all data sets will be projected to and calculations
# performed in.
#
##

sr_code = 3005 # NAD_1983_BC_Environment_Albers

### cp_presence_threshold, hu_presence_threshold, & layer_presence_threshold_file ###
#
# These define the threshold percent over which a layer is considerd present within an MPA
# This is defined as a decimal number from 0 - 1 (eg. 0.05 => 5%)
#
# Optionally layer_presence_threshold_file can be defined as the path to a CSV file defining
# these thresholds for each layer. The first column is the name of the layer and the second
# is the threshold percentage as a decimal number between 0 and 1. If a layer is not present
# in the CSV then the appropriate value will be used from cp_presence_threshold or
# hu_presence_threshold. If layer_presence_threshold_file is set to None then only those
# defined variables are used.
#
# This CSV should NOT have a header. Including one may result in an error or undefined
# behaviour.
#
##

cp_presence_threshold = 0.05
hu_presence_threshold = 0.05

layer_presence_threshold_file = None

### mpa_name_fields ###
#
# A list of strings that are possible field names containing MPA names
#
##

mpa_name_fields = ['NAME_E', 'Name_E']

### imatrix_path ###
#
# The path to the interaction matrix as a CSV. This CSV must have the the type of
# human use in the first column and conservation priorities in the third column
# such that when non-alphabetic characters (including white space) are stripped out
# and all characters are converted to lower case it matches the third element in
# HU dataset names and the fourth element in CP dataset names, respectively.
#
# For example a row reading like this:
#
# [Bottom Trawl, Demersal sharks/skates, Black skate / sandpaper skate, VERY HIGH]
#
# Would correspond to any HU feature beginning with the following:
#
#   mpatt_hu_bottomtrawl_...
#
# And any CP feature layer beginning with the following:
#
#   mpatt_eco_fish_blackskatesandpaperskate_...
#
# Finally any the values in the fourth column should be any of the following:
#
#   LOW, MEDIUM, HIGH, VERY HIGH
#
# Representing the consequence score.
#
# Finally, this CSV should have a header row. It will be discarded in reading but if it
# doesn't exist then you will miss the first row of your data.
##

imatrix_path = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\input\example_interaction_matrix.csv'

### output1_path & output2_path ###
#
# Paths to CSV files to be output from this script
#
##

output1_path = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\output\table1.csv'

output2_path = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\output\table2.csv'

### output3_path ###
#
# Path to CSV file to be output from this script
# Used for sliver threshold table
#
##

output3_path = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\output\table3_slivers.csv'

### complexFeatureClasses ###
#
# List of strings representing the feature class names of those features that
# are too complex to process as is. These get split into single part features
# which hopefully will solve most of those issues.
#
##

complexFeatureClasses = ['mpatt_eco_coarse_bottompatches_data']

### cleanUpTempData ###
#
# If True then temporary data is deleted after it is used
# set to False if you want to inspect the temp data after the script has run
# This might not be a good idea if you are doing a full run of the script
#
##

cleanUpTempData = False

### inclusion_matrix_path ###
#
# Path to the inclusion matrix file as CSV. The first row starting with the
# second cell should be MPATT HU feature class names. The first column starting
# with the second row should contain MPA names as found in the MPA feature
# classes.
#
# The where these MPAs and HU names intersect should be one of the following:
#
#   Y: This feature should be included in the MPA
#   N: This feature should NOT be included in the MPA
#   U: We are uncertain if the feature should be included in the MPA
#
# Any other value will be treated as blank and the script will determine inclusion
# based on spatial calculations
#
# The behaviour for what the script does when encountering these values can be
# further configured by setting the override_y, override_n, and override_u
# variables below
#

inclusion_matrix_path = r'C:\Users\jcristia\Documents\GIS\DFO\Python_Script\MPAT_CGA_Files_TESTING\20180206\input\example_inclusion_matrix.csv'

### override_y & _n & _u ###
#
# These variables set the behaviour for what should be done when testing for
# inclusion and there is a value for the given HU-MPA combo in the inclusion matrix.
#
# If override_y is False then an HU-MPA combo in the inclusion matrix with the value
# Y will be included in an MPA. If True it will allow the script to decide inclusion
# based on the spatial calculations
#
# If override_n is False then an HU-MPA combo in the inclusion matrix with the value
# N will NOT be included in the MPA. If True it will allow the script to decide
# inclusion based on the spatial calculations
#
# /!\ override_u BEHAVES DIFFERENTLY /!\
# If override_u is set to True then an HU-MPA combo in the inclusion matrix with the
# value U will be included in the MPA. If False then it will NOT be included in the
# MPA. If None then it will allow the script to decide inclusion based on the spatial
# calculations
#

override_y = False
override_n = True

override_u = None # This one behaves differently from _y and _n please read above and
                  # be careful when setting


######################
### Implementation ###
######################

###         ###
## Functions ##
###         ###

## fieldExists ##
#
# Checks if a field with a given name exists in the given feature class
#
# Returns True or False
#

def fieldExists(layer, field):
    for field in arcpy.ListFields(layer):
        if field.name == field:
            return True

    return False

## calculateArea ##
#
# Creates a double field in a feature class with the given name and
# populates it with the area of the associated feature
#

def calculateArea(layer, area_field):
    #if not fieldExists(layer, area_field):
    arcpy.AddField_management(layer, area_field, 'DOUBLE')

    arcpy.CalculateField_management(layer, area_field, '!shape.area!', 'PYTHON_9.3')

## calculateTotalArea ##
#
# Returns the total area of a feature class by summing up the values
# contained in the passed field
#

def calculateTotalArea(layer, area_field):
    summed_total = 0
    with arcpy.da.SearchCursor(layer, area_field) as cursor:
        for row in cursor:
            summed_total = summed_total + row[0]

    return summed_total
    
## prepareMPAs ##
#
# Gets MPA layers from mxd by reading the dataset name and merges them all
# into one file (mpa_merged_name). Also projects them into a consistent
# spatial reference (sr_code), puts all the MPA names into one column
# (mpa_name_field), and calculates the area of each (mpa_area_field)
#
        
def prepareMPAs(source_mxd, sr_code, mpa_area_field, mpa_area_attribute_section, final_mpa_fc_name, merged_name_field, mpa_name_fields, mpa_subregion_field, subregions_ALL, ecosections_layer):
    # Get MPA layers
    mxd = arcpy.mapping.MapDocument(source_mxd)
    layers = arcpy.mapping.ListLayers(mxd)
    mpa_layers = [lyr for lyr in layers if lyr.isFeatureLayer and lyr.datasetName.startswith('mpatt_mpa_')]

    # Load layers into workspace (and project)
    working_layers = []
    for lyr in mpa_layers:
        #project(lyr.dataSource, lyr.datasetName, arcpy.SpatialReference(sr_code))
        arcpy.Project_management(lyr.dataSource, lyr.datasetName,
                                 arcpy.SpatialReference(sr_code))
        working_layers.append(lyr.datasetName)

    # Set up field mappings (need a single consistent name field)
    fm = arcpy.FieldMappings()
    for lyr in working_layers:
        fm.addTable(lyr)

    fmap = arcpy.FieldMap()
    for lyr in working_layers:
        name_field = None
        for field in arcpy.ListFields(lyr):
            if field.name in mpa_name_fields:
                name_field = field.name
                break

        if name_field is None:
            raise ValueError('MPA Layer: {0} does not have field name in mpa_name_fields'.format(lyr))
                
        fmap.addInputField(lyr, name_field)

    nf = fmap.outputField
    nf.name = merged_name_field
    fmap.outputField = nf
    fm.addFieldMap(fmap)

    for field in fm.fields:
        if field.name != merged_name_field:
            fm.removeFieldMap(fm.findFieldMapIndex(field.name))

    # Perform merge and calculate area field
    arcpy.Merge_management(working_layers, "mpas_merged", fm)

    # Clean up the individual mpa files
    if cleanUpTempData:
        for layer in working_layers:
            arcpy.Delete_management(layer)

    # JC 20180204
    # Determine which subregion each MPA is in
    arcpy.AddField_management("mpas_merged", mpa_subregion_field,"TEXT")
    arcpy.Intersect_analysis(["mpas_merged",subregions_ALL], "mpa_sub_intersect", "NO_FID")
    with arcpy.da.UpdateCursor("mpas_merged", ["NAME_E", mpa_subregion_field]) as cursor_mpa:
        for mpa in cursor_mpa:
            mpa_name = (mpa[0].replace("'", "''")).encode('utf8') # the where clause requires double apostrophes
            where = "NAME_E = '{0}'".format(mpa_name)
            with arcpy.da.SearchCursor("mpa_sub_intersect", ["NAME_E", "subregion", "Shape_Area"], where) as cursor_mpasub:
                shpArea = 0.0
                subr = None
                for row in cursor_mpasub:
                    if row[2] > shpArea:
                        shpArea = row[2]
                        subr = row[1]
                mpa[1] = subr
                cursor_mpa.updateRow(mpa)
    arcpy.Delete_management("mpa_sub_intersect")
    
    # JC: changed field name to _TOTAL so this needs to be done before the intersect with ecosections
    # so that the area of the total mpa gets carried forward
    calculateArea("mpas_merged", mpa_area_field)

    # JC: intersect mpas and ecosections, then dissolve by mpa and ecosection
    arcpy.Intersect_analysis(["mpas_merged",ecosections_layer], "mpa_ecosect_intersect")
    arcpy.Dissolve_management("mpa_ecosect_intersect", final_mpa_fc_name, ["NAME_E", "ecosection"],[[mpa_subregion_field, "FIRST"],[mpa_area_field, "FIRST"]],"MULTI_PART")
    # Rename fields to get rid of the labels the dissolve appends to the beginning
    renameField(final_mpa_fc_name, 'FIRST_' + mpa_subregion_field, mpa_subregion_field, 'TEXT')
    renameField(final_mpa_fc_name, 'FIRST_' + mpa_area_field, mpa_area_field, 'DOUBLE')   
    # JC: add area field to calculate the area of each piece of an mpa in overlapping ecosections
    calculateArea(final_mpa_fc_name, mpa_area_attribute_section)
    # clean up merge and intersect datasets
    arcpy.Delete_management("mpas_merged")
    arcpy.Delete_management("mpa_ecosect_intersect")

    return final_mpa_fc_name

## buildScalingDict ##
#
# Reads a two column CSV where the first column is
# an mpatt dataset name and the second is the name
# of the field that contains the scaling factor used
# to scale a features area in that dataset before it
# is determined whether or not it exists within an MPA
#
# Returns a dict where the dataset name points to the
# scaling factor
#

def buildScalingDict(scaling_attribute_file):
    scaling_fields = {}

    with open(scaling_attribute_file, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            fc_name = row[0]
            scaling_attribute = row[1]

            scaling_fields[fc_name] = scaling_attribute

    return scaling_fields

## loadLayer ##
#
# Copies a layer into the temporary workspace, reprojects it, calculates the area
# and creates a consistently named scaling attribute
#
# If is_complex == True the layer is split to single part features before other
# calculations are performed. This will often make processes work that would fail
# otherwise
#
# Returns the output layer name which can be different
#

def loadLayer(source_mxd, layer_name, sr_code, new_bc_area_field, new_bc_total_area_field,
              scaling_dict, scaling_attribute, new_scaling_field, is_complex):
    if detailed_status:
        print 'Loading ' + layer_name
    
    # Find layer in mxd
    mxd = arcpy.mapping.MapDocument(source_mxd)
    layer = arcpy.mapping.ListLayers(mxd, layer_name)[0]

    # Load layer into workspace and reproject
    working_layer = layer.datasetName
    orig_name = working_layer

    arcpy.Project_management(layer.dataSource, layer.datasetName,
                             arcpy.SpatialReference(sr_code))
    
    if is_complex:
        if detailed_status:
            print '...Exploding complex feature class'
        arcpy.MultipartToSinglepart_management(working_layer, working_layer+'_c')

        # Clean up
        if cleanUpTempData:
            arcpy.Delete_management(working_layer)
        
        working_layer = working_layer+'_c'

    # Create consistent scaling field
    arcpy.AddField_management(working_layer, new_scaling_field, 'DOUBLE')

    # If layer is in scaling_dict use that attribute for scaling_attribute
    if scaling_dict is not None and working_layer in scaling_dict:
        scaling_attribute = scaling_dict[working_layer]

    # If scaling_attribute is set and it exists in the feature class
    # copy into new_scaling_field
    if scaling_attribute is not None and len(
            arcpy.ListFields(working_layer, scaling_attribute)) >= 1:
        arcpy.CalculateField_management(working_layer, new_scaling_field,
                                        '!{0}!'.format(scaling_attribute), 'PYTHON_9.3')
    else: # If no scaling then just use 1 for scaling
        arcpy.CalculateField_management(working_layer, new_scaling_field,
                                        '1', 'PYTHON_9.3')
    
    keep_fields = [new_scaling_field, 'ecosection'] # JC: added ecosection to this list

    # Delete fields that aren't important
    for field in arcpy.ListFields(working_layer):
        # Don't delete Object ID or Geometry 
        if field.type in ['OID','Geometry']:
            continue

        # Don't try to delete required fields
        if field.required:
            continue

        # Don't delete fields in keep_fields
        if field.name not in keep_fields:
            arcpy.DeleteField_management(working_layer, field.name)

    # Add new area fields
    arcpy.AddField_management(working_layer, new_bc_area_field, "DOUBLE")
    arcpy.AddField_management(working_layer, new_bc_total_area_field, "DOUBLE")

    # Calculate feature area and total area
    calculateArea(working_layer, new_bc_area_field)
    total_area = calculateTotalArea(working_layer, new_bc_area_field)
    arcpy.CalculateField_management(working_layer, new_bc_total_area_field, total_area, 'PYTHON_9.3')

    if working_layer != orig_name:
        if arcpy.Exists(orig_name):
            arcpy.Rename_management(orig_name, orig_name + '_original')
        arcpy.Rename_management(working_layer, orig_name)
        
    return orig_name

## loadRegionLayer ##
#
# Similar to loadLayer above but doesn't add a scaling attribute (not needed)
# 

def loadRegionLayer(source_mxd, layer_name, sr_code, new_bc_area_field, new_bc_total_area_field):
    if detailed_status:
        print 'Loading ' + layer_name
        
    # Find layer in mxd
    mxd = arcpy.mapping.MapDocument(source_mxd)
    layer = arcpy.mapping.ListLayers(mxd, layer_name)[0]

    # Load layer into workspace and reproject
    working_layer = layer.datasetName
    arcpy.Project_management(layer.dataSource, layer.datasetName,
                             arcpy.SpatialReference(sr_code))

    # Add new area fields
    arcpy.AddField_management(working_layer, new_bc_area_field, "DOUBLE")
    arcpy.AddField_management(working_layer, new_bc_total_area_field, "DOUBLE")

    # Calculate feature area and total area
    calculateArea(working_layer, new_bc_area_field)
    total_area = calculateTotalArea(working_layer, new_bc_area_field)
    arcpy.CalculateField_management(working_layer, new_bc_total_area_field, total_area, 'PYTHON_9.3')

    return working_layer

## buildThresholdDict ##
#
# Reads a csv where the first column is an mpatt dataset name
# and the second is the threshold used to determine whether it
# is present in an MPA or not
#
# Returns a dict where the key is an mpatt dataset name that
# points to the threshold for that layer
#

def buildThresholdDict(layer_presence_threshold_file):
    thresholds = {}

    with open(layer_presence_threshold_file, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            fc_name = row[0]
            layer_threshold = row[1]

            thresholds[fc_name] = layer_treshold

    return thresholds


## renameField ##
#
# Adds a new field with the desired name, copies values from an old
# field with an undesireable name, and deletes that old field
#

def renameField(working_layer, ifield, ofield, ftype):
    arcpy.AddField_management(working_layer, ofield, ftype)
    arcpy.CalculateField_management(working_layer, ofield, '!{0}!'.format(ifield), 'PYTHON_9.3')
    arcpy.DeleteField_management(working_layer, ifield)

## readMPAInclusionMatrix ##
#
# Reads a CSV structured like a matrix where the first row contains mpatt feature class names
# and the first column contains MPA names matching those in the MPA feature classes. The values
# are any of the following:
#
# Y: This feature should be included in the MPA
# N: This feature should NOT be included in the MPA
# U: We are uncertain if the feature should be included in the MPA
#
# Any other value will be treated as if it were left a blank
#
# Should only be used for HU features

def readMPAInclusionMatrix(mpath):
    inclusion_matrix = {}
    with open(mpath, 'rb') as csvfile:
        reader = csv.reader(csvfile)

        # Read header first
        header = reader.next()

        for row in reader:
            # Get mpa from first column
            mpa = row[0]
            inclusion_matrix[mpa] = {}

            # Iterate through row skipping first col
            for i in range(1, len(row)):
                # Get feature class name from header
                fc_name = header[i]
                # Set inclusion value to whatever value is in the file unless its blank
                inclusion_matrix[mpa][fc_name] = row[i].strip() if row[i].strip() in ('Y', 'N', 'U') else None
                
    return inclusion_matrix

## shouldInclude ##
#
# Tests to see if a feature belongs in an MPA guided by the inclusion matrix
#

def shouldInclude(pct_in_mpa, threshold, im, fc, mpa):
    # If mpa is not in inclusion matrix use conventional inclusion test
    if mpa not in im:
        return pct_in_mpa > threshold

    # If fc not in inclusion matrix use conventional inclusion test
    if fc not in im[mpa]:
        return pct_in_mpa > threshold

    # Get inclusion value
    i_val = im[mpa][fc]

    # If inclusion value was blank use conventional inclusion test
    if i_val is None:
        return pct_in_mpa > threshold

    # If inclusion value is Y and override is disabled then include it
    if i_val is 'Y' and not override_y:
        return True

    # See above but for N
    if i_val is 'N' and not override_n:
        return False

    # If value is U do what override asks
    if i_val is 'U' and override_u is not None:
        return override_u

    # Otherwise override whatever value is in i_val with conventional test
    return pct_in_mpa > threshold

## process_geometry ##
#
# Does the geometric heavy lifting. Determines what area of a feature falls in each MPA.
# Also performs a subregional analysis if a region_layer is provided.
#
# Returns a feature class with the adjusted and clipped area of the feature class
# and the original area of the feature class in addition to information about the enclosing
# MPA and percentages comparing the clipped/adjusted size to the MPA size and the original
# size of the fc
#
    
def process_geometry(base_layer, final_mpa_fc_name, clipped_adjusted_area, scaling_attribute,
                     mpa_name_attribute, mpa_area_attribute, new_bc_total_area_field,
                     pct_of_mpa_field, pct_of_total_field, mpa_subregion_field, mpa_area_attribute_section,
                     clipped_adj_area_mpaTotal, pct_of_mpa_field_Total):
            
    working_intersect = base_layer + '_Intersect'

    # Intersect with by MPAs and explode to singlepart
    if detailed_status:
        print '...Intersecting ' + base_layer
    arcpy.Intersect_analysis([base_layer, final_mpa_fc_name], working_intersect)

    # Calculate area after clipping and adjust it by the scaling factor
    # Do this before dissolving because otherwise you can't capture scaling factors
    # or overlapping area
    arcpy.AddField_management(working_intersect, clipped_adjusted_area, 'DOUBLE')
    arcpy.CalculateField_management(working_intersect, clipped_adjusted_area,
                                    '!shape.area!*!{0}!'.format(scaling_attribute), 'PYTHON_9.3')

    # Dissolve by mpa_name_attribute field summing adjusted area
    working_dissolved = base_layer + '_Dissolved'
    
    if detailed_status:
        print '...Dissolving ' + base_layer
    arcpy.Dissolve_management(working_intersect, working_dissolved, [mpa_name_attribute, "ecosection"],
                              [[clipped_adjusted_area, 'SUM'], [new_bc_total_area_field, 'FIRST'],
                               [mpa_area_attribute, 'FIRST'], [mpa_area_attribute_section, 'FIRST'],
                              [mpa_subregion_field, 'FIRST']])

    # Rename fields for simplicities sake
    renameField(working_dissolved, 'SUM_' + clipped_adjusted_area, clipped_adjusted_area, 'DOUBLE')
    renameField(working_dissolved, 'FIRST_' + new_bc_total_area_field, new_bc_total_area_field, 'DOUBLE')
    renameField(working_dissolved, 'FIRST_' + mpa_area_attribute, mpa_area_attribute, 'DOUBLE')
    renameField(working_dissolved, 'FIRST_' + mpa_area_attribute_section, mpa_area_attribute_section, 'DOUBLE')
    renameField(working_dissolved, 'FIRST_' + mpa_subregion_field, mpa_subregion_field, 'TEXT')

    
    arcpy.AddField_management(working_dissolved, pct_of_mpa_field, 'DOUBLE')
    arcpy.AddField_management(working_dissolved, clipped_adj_area_mpaTotal, 'DOUBLE')
    arcpy.AddField_management(working_dissolved, pct_of_mpa_field_Total, 'DOUBLE')
    arcpy.AddField_management(working_dissolved, pct_of_total_field, 'DOUBLE')

    # Calculate percentages
    arcpy.CalculateField_management(working_dissolved, pct_of_mpa_field,
                                    '!{0}!/!{1}!'.format(clipped_adjusted_area,mpa_area_attribute),
                                    'PYTHON_9.3')
    arcpy.CalculateField_management(working_dissolved, pct_of_total_field,
                                    '!{0}!/!{1}!'.format(clipped_adjusted_area,new_bc_total_area_field),
                                    'PYTHON_9.3')
    
    # JC: calculate new total fields
    # get unique list of mpas
    mpa_list = []
    with arcpy.da.SearchCursor(working_dissolved, [mpa_name_attribute]) as cursor:
        for row in cursor:
            if row[0] not in mpa_list:
                mpa_list.append(row[0])
    # add up feature areas by mpa
    for mpa in mpa_list:
        mpa_name = (mpa.replace("'", "''")).encode('utf8') # the where clause requires double apostrophes
        where = "{0} = '{1}'".format(mpa_name_attribute, mpa_name)
        with arcpy.da.UpdateCursor(working_dissolved, [clipped_adjusted_area, clipped_adj_area_mpaTotal], where) as cursor:
            sum_area = 0.0
            for row in cursor:
                sum_area += row[0]
            cursor.reset()
            for row in cursor:
                row[1] = sum_area
                cursor.updateRow(row)

    arcpy.CalculateField_management(working_dissolved, pct_of_mpa_field_Total,
                                    '!{0}!/!{1}!'.format(clipped_adj_area_mpaTotal,mpa_area_attribute),
                                    'PYTHON_9.3')

    # Clean up
    if cleanUpTempData:
        for layer in arcpy.ListFeatureClasses(base_layer + '_*'):
            if layer != working_dissolved:
                arcpy.Delete_management(layer)
        
    return working_dissolved

## calculate_presence ##
#
# Returns a dict with various info about the passed layers presence within each
# MPA. The first key in the dict is the mpa name which points to another dict.
# This dict has the following keys with the following values:
#
#     'clip_area'     -> The adjusted and clipped area of the layer in the mpa
#     'orig_area'     -> The original area of the layer
#     'mpa_area'      -> The area of the MPA
#     'region_area'   -> The area of the clipped region (if applicable otherwise None)
#     'pct_in_mpa'    -> clip_area / mpa_area
#     'pct_of_region' -> clip_area / region_area (if applicable otherwise None)
#     'pct_of_total'  -> clip_area / orig_area

def calculate_presence(working_layer, final_mpa_fc_name, clipped_adjusted_area,
                       pct_of_total_field, pct_of_mpa_field, mpa_name_attribute,
                       scaling_attribute, threshold, subregion, imatrix, mpa_subregion_field, mpa_area_attribute_section, clipped_adj_area_mpaTotal, pct_of_mpa_field_Total):
    mpas = {}
    sliver_freq = {} # added 20180205 to get sliver frequencies

    # JC: this line doesn't make sense. For one, it will never be none, since if there is no
    # subregion code then 'region' gets passed to subregion.
    # Also, why is it recalculating this? We already know the total area. Is it just easier than
    # grabbing the value of the first field? (this is probably it - it needs that value to write
    # to the dictionary).
    # Also, it should not pass 'new_bc_total_are_field'
    # Lastly, even though region_area is used in some calculations, ultimately, none of those results
    # are ever outputted anywhere.
    # JC: changing the second variable from 'new_bc_total_area_field' to 'new_bc_area_field'
    region_area = calculateTotalArea(working_layer,
                                     new_bc_area_field) if subregion is not None else None

    # Crunch the geometry for the whole region
    processed_layer = process_geometry(working_layer, final_mpa_fc_name, clipped_adjusted_area,
                                       scaling_attribute, mpa_name_attribute, mpa_area_attribute,
                                       new_bc_total_area_field, pct_of_mpa_field, pct_of_total_field,
                                       mpa_subregion_field, mpa_area_attribute_section, clipped_adj_area_mpaTotal,
                                      pct_of_mpa_field_Total)

    # Read the statistics for the whole region into a dict
    with arcpy.da.SearchCursor(
            processed_layer,
            [mpa_name_attribute,mpa_area_attribute,pct_of_mpa_field,pct_of_total_field,
             new_bc_total_area_field,clipped_adjusted_area, "ecosection", mpa_subregion_field,
             mpa_area_attribute_section, clipped_adj_area_mpaTotal, pct_of_mpa_field_Total]
    ) as cursor:
        # i.e. for each mpa which technically has hu/cp in it
        for row in cursor:
            mpa_name, mpa_area, pct_of_mpa = row[0], row[1], row[2]
            pct_of_total, hucp_og_area, hucp_clip_area = row[3], row[4], row[5]
            ecosect, subreg_mpa, mpa_area_ecosect  = row[6], row[7], row[8]
            hucp_clip_area_mpaTotal, pct_of_mpa_Total = row[9], row[10]

            # each HU/CP is a dict w/ info on its name, clipped area, and total area of
            # the original layer
            #
            # Checks if hu/cp makes up greater than 5% (or whatever) of mpa
            datasetname = working_layer if subregion is not None else '_'.join(working_layer.split('_')[:-1])
            
            if mpa_name not in sliver_freq:
                sliver_freq[mpa_name] = {'pct_overlap_cphu_mpa': pct_of_mpa_Total}
                # this should only need to be written once, even if there are multiple features for each mpa

            if shouldInclude(pct_of_mpa_Total, threshold, imatrix, datasetname, mpa_name):
                pct_of_region = (hucp_clip_area / region_area) if region_area is not None else None
                if mpa_name not in mpas:
                    mpas[mpa_name] = {}
                mpas[mpa_name][ecosect] = {'subregion': subreg_mpa,
                                  'clip_area': hucp_clip_area,
                                  'orig_area': hucp_og_area,
                                  'mpa_area': mpa_area,
                                  'region_area': region_area,
                                  'pct_in_mpa': pct_of_mpa,
                                  'pct_of_region': pct_of_region,
                                  'pct_of_total': pct_of_total}
              
    # Clean up workspace
    if cleanUpTempData:
        arcpy.Delete_management(working_layer)
        arcpy.Delete_management(processed_layer)
            
    return mpas, sliver_freq

## calcEffectivenessScore ##
#
# Takes the number of interactions for a cp broken down by severity and spits out an effectiveness score
#

def calcEffectivenessScore(num_high, num_mod, num_low):
    if num_high > 0 or num_mod > 2: # High
        return 0.0
    elif num_mod == 2: # Moderate-High
        return 0.24
    elif num_mod == 1: # Moderate
        return 0.6
    elif num_low > 0: # Low impact
        return 0.85
    else: # Negligible
        return 1.0


## countInteractions ##
#
# Counts up the interactions for easy reading into calcEffectivenessScore
#

def countInteractions(i_list):
    num_high = 0
    num_mod = 0
    num_low = 0
    
    for interaction in i_list:
        if interaction == 'HIGH':
            num_high = num_high + 1
        elif interaction == 'MODERATE':
            num_mod = num_mod + 1
        elif interaction == 'LOW':
            num_low = num_low + 1
            
    return (num_high, num_mod, num_low)

## loadInteractionsMatrix ##
#
# Reads the interactions matrix from a csv file. An external library could be used
# to read it from the Excel workbook but that seemed unnecessary for this task.
#
# Returns one of the more straightforward dicts of this script. The first key is
# the CP dataset name and the second key is the HU dataset name. The value is the
# interaction severity
# 

def loadInteractionsMatrix(imatrix_path):
    imatrix = {}
    
    with open(imatrix_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        reader.next()

        regex = re.compile('[^a-zA-Z]')

        for row in reader:
            # Convert matrix entries to lower case and remove spaces
            # and non-alphabetic ccharacters. In theory this will make
            # them match up to the layer dataset names
            #
            # eg. Tufted puffins -> tuftedpuffins unfortunately the
            # mpatt dataset is called mpatt_eco_birds_tuftedpuffin_colonies_seasketch
            # without the s
            #
            hu = regex.sub('', row[0]).lower()
            cp = regex.sub('', row[2]).lower()
            interaction = row[3]

            # The file uses a different conventions than the docs
            # I was working off of
            if interaction == 'VERY HIGH':
                interaction = 'HIGH'
                
            if interaction == 'MEDIUM':
                interaction = 'MODERATE'

            if cp not in imatrix:
                imatrix[cp] = {}

            imatrix[cp][hu] = interaction         

    return imatrix

## determineInteraction ##
#
# Get the relevent part of the dataset names and return the interaction
# from the imatrix
#

def determineInteraction(imatrix, cp, hu):
    cp = cp.split('_')[3]
    hu = hu.split('_')[2]
    
    if cp in imatrix:
        if hu in imatrix[cp]:
            return imatrix[cp][hu]
    else:
        print cp + " not in imatrix"
        # I don't want to make this an error since it is possible that a cp has no interactions
        # Therefore it's very important that names match between files and the imatrix

    return None

## identifyInteractions ##
#
# Finds HUs and CPs in the same MPA and checks if they have an interaction
# Builds a dict with interaction scaling factors for each CP in each MPA
#

def identifyInteractions(hu_in_mpas, cp_in_mpas, imatrix):
    cp_in_mpa_i = {}

    for mpa in hu_in_mpas:
        if mpa not in cp_in_mpas:
            continue

        if mpa not in cp_in_mpa_i:
            cp_in_mpa_i[mpa] = {}

        for ecosection in cp_in_mpas[mpa]:
            # we only need to know the interaction once. The ecosection doesn't matter here.
            for cp in cp_in_mpas[mpa][ecosection]:
                if cp not in cp_in_mpa_i[mpa]:
                        cp_in_mpa_i[mpa][cp] = {'interactions': [],
                                                'eff_score': None}
                else:
                    continue  # we only need the cp once per mpa, so if we have already encountered it then skip
                        
                for hu in hu_in_mpas[mpa]:
                    interaction = determineInteraction(imatrix, cp, hu)
    
                    if interaction is not None:
                        cp_in_mpa_i[mpa][cp]['interactions'].append(interaction)

    return cp_in_mpa_i

## prepareOutputTable1 ##
#
# Pulls all the data together to make a dict that can be used to create the final output
# Calculates effectiveness scores and uses it to scale the CPs
#
# The returned dict is structured like so: o_table_1[ MPA NAME ][ REGION ][ CP ]
# this points to a dict that has the following keys:
#
# 'mpa_area'     -> area of the enclosing mpa
# 'og_area'      -> total area of the original CP
# 'uscaled_area' -> area of the clipped and adjusted CP in the MPA
# 'scaled_area'  -> uscaled_area but multiplied by the CPs effectiveness score
# 'pct_of_mpa'   -> scaled_area / mpa_area
# 'pct_of_og'    -> scaled_area / og_area


def prepareOutputTable1(cp_in_mpa_i, cp_in_mpas):
    o_table_1 = {}

    ecosections = ["Johnstone Strait", "Continental Slope", "Dixon Entrance", "Strait of Georgia", "Juan de Fuca Strait", "Queen Charlotte Strait", "North Coast Fjords", "Hecate Strait", "Queen Charlotte Sound", "Vancouver Island Shelf", "Transitional Pacific", "Subarctic Pacific"]
    
    for mpa in cp_in_mpa_i:
        if mpa not in o_table_1:
            o_table_1[mpa] = {}

        for cp in cp_in_mpa_i[mpa]:
            for ecosection in ecosections:
                if ecosection in cp_in_mpas[mpa] and cp in cp_in_mpas[mpa][ecosection]:                    
                    if ecosection not in o_table_1[mpa]:
                        o_table_1[mpa][ecosection] = {}

                    # Pre populate dict with already known values
                    if cp not in o_table_1[mpa][ecosection]:
                        o_table_1[mpa][ecosection][cp] = {'mpa_area': cp_in_mpas[mpa][ecosection][cp]['mpa_area'],
                                                      'og_area': cp_in_mpas[mpa][ecosection][cp]['orig_area'],
                                                      'uscaled_area': cp_in_mpas[mpa][ecosection][cp]['clip_area'],
                                                      'scaled_area': None,
                                                      'pct_of_mpa': None,
                                                      'pct_of_og': None,
                                                      'subregion': cp_in_mpas[mpa][ecosection][cp]['subregion']}

                    # Calculate effectiveness
                    num_high, num_mod, num_low = countInteractions(cp_in_mpa_i[mpa][cp]['interactions'])

                    cp_in_mpa_i[mpa][cp]['eff_score'] = calcEffectivenessScore(num_high,
                                                                               num_mod,
                                                                               num_low)

                    # Rescale areas and calculate new percentages
                    eff_score = cp_in_mpa_i[mpa][cp]['eff_score']
                    unscaled_area = o_table_1[mpa][ecosection][cp]['uscaled_area']
                    o_table_1[mpa][ecosection][cp]['scaled_area'] = eff_score * unscaled_area

                    scaled_area = o_table_1[mpa][ecosection][cp]['scaled_area']
                    mpa_area = o_table_1[mpa][ecosection][cp]['mpa_area']
                    og_area = o_table_1[mpa][ecosection][cp]['og_area']

                    o_table_1[mpa][ecosection][cp]['pct_of_mpa'] = scaled_area / mpa_area
                    o_table_1[mpa][ecosection][cp]['pct_of_og'] = scaled_area / og_area
                
    return o_table_1

## writeOutputTable1 ##
#
# Writes the final output to disk
#

def writeOutputTable1(otable, opath):
    # Get a list of all the CPs (i.e. columns) needed
    cp_list = []
    for mpa in otable:
        for ecosection in otable[mpa]:
            for cp in otable[mpa][ecosection]:
                if cp not in cp_list:
                    cp_list.append(cp)

    # Sort that list so it's easier to find something            
    cp_list.sort()

    with open(opath, 'wb') as f:
        w = csv.writer(f)

        # Write header with extra cols at start (for MPA names, regions, and ecosections)
        w.writerow(['MPA','Subregion','Ecosection']+cp_list)

        for mpa in otable:
            for ecosection in otable[mpa]:
                # Build empty row
                row = ['' for i in range(0, len(cp_list))]

                # Put value where it belongs in the list
                for cp in otable[mpa][ecosection]:
                    pct_of_og = otable[mpa][ecosection][cp]['pct_of_og']
                    row[cp_list.index(cp)] = pct_of_og
                subregion = otable[mpa][ecosection][cp]['subregion']  # the subregion is the same for each cp within an mpa, so it doesn't matter which one I pull from 
                w.writerow([mpa.encode('utf8'), subregion, ecosection] + row)


def createOutputTable2(o_table_1):
    table2 = {}

    fields = ['original', 'protected', 'pct']

    for mpa in o_table_1:
        for region in o_table_1[mpa]:
            for cp in o_table_1[mpa][region]:
                cp_data = o_table_1[mpa][region][cp]

                if cp not in table2:
                    table2[cp] = {}

                if region not in table2[cp]:
                    table2[cp][region] = {}
                    
                for field in fields:
                    if field not in table2[cp][region]:
                        table2[cp][region][field] = 0.0

                # Sum up protected area from all MPAs for CP
                table2[cp][region]['original'] = cp_data['og_area']
                table2[cp][region]['protected'] = table2[cp][region]['protected'] \
                                                 + cp_data['scaled_area']

    # Calculate percentages
    for cp in table2:
        for region in table2[cp]:
            if table2[cp][region]['original'] != 0:
                table2[cp][region]['pct'] = table2[cp][region]['protected']/table2[cp][region]['original']

    return table2


def writeOutputTable2(o_table_2, ofile):
    cols = ['region','CC','NC','NCVI','HG']

    with open(ofile, 'wb') as f:
        w = csv.writer(f)

        # Write header
        w.writerow(['']+cols)

        for cp in o_table_2:
            row = ['' for i in range(len(cols))]
            for sr in o_table_2[cp]:
                row[cols.index(sr)] = o_table_2[cp][sr]['pct']

            w.writerow([cp] + row)

def writeOutputTable3(percent_overlap, output3_path):
    cols = ['mpa','type','cp_hu','percent_overlap']

    with open(output3_path, 'wb') as f:
        w = csv.writer(f)

        # Write header
        w.writerow(cols)

        for mpa in percent_overlap:
            for layer_type in percent_overlap[mpa]:
                for cphu in percent_overlap[mpa][layer_type]:
                        pct_o = percent_overlap[mpa][layer_type][cphu]['pct_overlap_cphu_mpa']
                        w.writerow([mpa.encode('utf8'), layer_type, cphu, pct_o])

  ##               ##
###  Program start  ###
  ##               ##
        
# Generate unique name for temp gdb and make it the workspace
i = 0;
while arcpy.Exists(os.path.join(working_gdb_folder, 'temp{0}.gdb'.format(str(i)))):
    i = i + 1
    
working_gdb = os.path.join(working_gdb_folder, 'temp{0}.gdb'.format(str(i)))

arcpy.CreateFileGDB_management(os.path.dirname(working_gdb), os.path.basename(working_gdb))
arcpy.env.workspace = working_gdb

#####
### Load Ecosection layer into workspace
### JC addition 20180207
#####

if print_status:
    print "Preparing Ecosections"

new_bc_area_field = 'etp_bc_area'
new_bc_total_area_field = 'etp_bc_total_area'
new_scaling_field = 'etp_scaling'

layer_list = arcpy.mapping.ListLayers(arcpy.mapping.MapDocument(source_mxd))
for lyr in layer_list:
    if lyr.isFeatureLayer and (lyr.datasetName.startswith('mpatt_eco_coarse_ecosections')):
        ecosections = lyr
ecosections_layer = loadLayer(source_mxd, ecosections.name, sr_code,
                              new_bc_area_field, new_bc_total_area_field,
                              None, scaling_attribute, new_scaling_field,
                              None)

#####
### Load subregional layer into workspace
### This is the one layer that has all the subregions in it.
### It is used to determine which subregion each MPA is in
#####

layer_list = arcpy.mapping.ListLayers(arcpy.mapping.MapDocument(source_mxd))
for lyr in layer_list:
   if lyr.isFeatureLayer and (lyr.datasetName.startswith('mpatt_rgn_subregions')):
       subregions_ALL = loadRegionLayer(source_mxd, lyr.name,
                                                sr_code, new_bc_area_field,
                                                new_bc_total_area_field)


#####
### Load MPA layers into workspace, create consistent name attribute, and merge together
#####

if print_status:
    print "Preparing MPAs"

mpa_area_attribute = 'etp_mpa_area_TOTAL'
merged_name_field = 'NAME_E'
final_mpa_fc_name = 'mpas'
mpa_subregion_field = 'subregion_mpa'
mpa_area_attribute_section = 'etp_mpa_area_SECTION'


final_mpa_fc_name = prepareMPAs(source_mxd, sr_code, mpa_area_attribute, mpa_area_attribute_section,
                                final_mpa_fc_name, merged_name_field, mpa_name_fields, mpa_subregion_field, subregions_ALL, ecosections_layer)

#####
### Load subregional layers into workspace
#####

layer_list = arcpy.mapping.ListLayers(arcpy.mapping.MapDocument(source_mxd))
layer_list = [lyr for lyr in layer_list if lyr.isFeatureLayer \
              and (lyr.datasetName.startswith('mpatt_rgn_subregion_'))]

rlayers = {}

for layer in layer_list:
    subregion = layer.datasetName.split('_')[3]
    rlayers[subregion] = loadRegionLayer(source_mxd, layer.name,
                                         sr_code, new_bc_area_field,
                                         new_bc_total_area_field)


#####
### Load HU/CP layers into workspace, calculate areas etc
#####

# Load attribute scaling file if necessary
scaling_dict = None
if scaling_attribute_file is not None:
    scaling_dict = buildScalingDict(scaling_attribute_file)

threshold_dict = None
if layer_presence_threshold_file is not None:
    threshold_dict = buildThresholdDict(layer_presence_threshold_file)

inclusion_matrix = readMPAInclusionMatrix(inclusion_matrix_path)

# Generate layer list based on dataset names
layer_list = arcpy.mapping.ListLayers(arcpy.mapping.MapDocument(source_mxd))
layer_list = [lyr for lyr in layer_list if lyr.isFeatureLayer \
              and (lyr.datasetName.startswith('mpatt_eco_') \
                   or lyr.datasetName.startswith('mpatt_hu_'))]

arcpy.env.overwriteOutput = True

clipped_adjusted_area = 'etp_ac_area_adj'
pct_of_total_field = 'pct_of_total'
pct_of_mpa_field = 'pct_of_mpa'
# JC fields added
clipped_adj_area_mpaTotal = 'etp_ac_area_adj_mpaTotal'
pct_of_mpa_field_Total = 'pct_of_mpa_Total'

hu_in_mpas,cp_in_mpas = {}, {}
percent_overlap = {}
for lyr in layer_list:
    if print_status:
        print "Processing " + lyr.name + " for presence in MPAs"

    # Load layer into memory, reprojecting to albers, calculate areas etc
    # If a layer is complex and causes processing to fail populate
    # complexFeatureClasses above and hopefully that fixes it
    is_complex = lyr.name in complexFeatureClasses
    working_layer = loadLayer(source_mxd, lyr.name, sr_code,
                              new_bc_area_field, new_bc_total_area_field,
                              scaling_dict, scaling_attribute, new_scaling_field,
                              is_complex)

    layer_type = 'cp' if working_layer.startswith('mpatt_eco_') else 'hu'

    # Set to default hu/cp presence threshold and overwrite with value in threshold_dict
    # if possible
    threshold = hu_presence_threshold if layer_type == 'hu' else cp_presence_threshold
    if threshold_dict is not None and working_layer in threshold_dict:
        threshold = threshold_dict[working_layer]

    # Check last element in layer dataset name to see if has been subregionally clipped
    # and get that subregion layer
    subregion = working_layer.split('_')[-1]
    rlayer = rlayers[subregion] if subregion in rlayers else None
    subregion = 'region' if rlayer is None else subregion
    
    # Determine if in which MPAs and calculate statistics
    mpa_presence, sliver_freq = calculate_presence(working_layer, final_mpa_fc_name, clipped_adjusted_area,
                                      pct_of_total_field, pct_of_mpa_field, merged_name_field,
                                      new_scaling_field, threshold, subregion, inclusion_matrix,
                                      mpa_subregion_field, mpa_area_attribute_section, clipped_adj_area_mpaTotal,
                                      pct_of_mpa_field_Total)


    # If subregion fc split off that subregion tag on the fc name
    if subregion != 'region':
        working_layer = '_'.join(working_layer.split('_')[:-1])

    if layer_type == 'hu':
        for mpa in mpa_presence:            
            if mpa not in hu_in_mpas:
                hu_in_mpas[mpa] = {}
            hu_in_mpas[mpa][working_layer] = mpa_presence[mpa]
            # JC: all we need to know is if an hu occurs in an mpa. We don't care about its area measurements at this point, so I can just keep this as is.
    else:        
        for mpa in mpa_presence:
            if mpa not in cp_in_mpas:
                cp_in_mpas[mpa] = {}
            for ecosection in mpa_presence[mpa]:
                if ecosection not in cp_in_mpas[mpa]:
                    cp_in_mpas[mpa][ecosection] = {}
                cp_in_mpas[mpa][ecosection][working_layer] = mpa_presence[mpa][ecosection]

    # Populate percent_overlap dictionary (added 20180205)
    for mpa in sliver_freq:
        if mpa not in percent_overlap:
            percent_overlap[mpa] = {}
        if layer_type not in percent_overlap[mpa]:
            percent_overlap[mpa][layer_type] = {}
        percent_overlap[mpa][layer_type][working_layer] = sliver_freq[mpa]


# Tack in dummy data for HU that should be in each MPA according to the interaction matrix
# but didn't have spatial data that sufficiently intersected
for mpa in inclusion_matrix:
    for hu in inclusion_matrix[mpa]:
        if inclusion_matrix[mpa][hu] == 'Y' or (inclusion_matrix[mpa][hu] == 'U' and override_u is True):  # this OR statement was an addition and has not been tested yet
            if mpa not in hu_in_mpas:
                hu_in_mpas[mpa] = {}

            if hu not in hu_in_mpas[mpa]:    
                hu_in_mpas[mpa][hu] = {'ecosect_placeholder': # I dont think these values or the ecosection name matters here since all we need to know is if an hu occurs in an mpa.
                                       {'clip_area': 1,
                                       'orig_area': 1,
                                       'mpa_area': 1,
                                       'region_area': 1,
                                       'pct_in_mpa': 1,
                                       'pct_of_region': 1,
                                       'pct_of_total': 1}}
# Clean up
if cleanUpTempData:
    arcpy.Delete_management(working_gdb)
    
#####
### Find HU-CP interactions within MPAs and write output table 1
#####

imatrix = loadInteractionsMatrix(imatrix_path)

cp_in_mpa_i = identifyInteractions(hu_in_mpas, cp_in_mpas, imatrix)

o_table_1 = prepareOutputTable1(cp_in_mpa_i, cp_in_mpas)

writeOutputTable1(o_table_1, output1_path)

#####
### Create and write output table 2
#####

o_table_2 = createOutputTable2(o_table_1)

writeOutputTable2(o_table_2, output2_path)

#####
### Write percent overlap (sliver) table
#####

writeOutputTable3(percent_overlap, output3_path)