# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 20:18:36 2020

@author: grandgrue
"""

import pandas as pd
import numpy as np
import urllib.request, json 
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import datetime

# general settings
today = datetime.date.today()

# api settings
ckanurl = "https://data.stadt-zuerich.ch"
queryapi = ckanurl + "/api/3/action/package_search?q=&rows=999"

# file settings
orgcsv = "organizations.csv"
orgmapcsv = "org-mapping.csv"
err_miss_map = "error_missing-mapping.csv"
excel_out = "Report OGD Datensätze nach Organisationseinheit.xlsx"

# image settings
image_in = "stzh-org-template.png"
image_out = "Report OGD Datensätze nach Departement und Dienstabteilung.png"
box_width = 160
padding_top_dept = -50
padding_right_dept = 5
padding_top_da = 13
padding_right_da = 3
font_dept = ImageFont.truetype("arial.ttf", 28, encoding="unic")
font_da = ImageFont.truetype("arial.ttf", 24, encoding="unic")
font_state = ImageFont.truetype("arial.ttf", 10, encoding="unic")
show_error = True # default: True / set to False to remove error from image


# PHASE 1: CKAN-API GET INFORMATION ABOUT ALL DATASETS
# query all packages
with urllib.request.urlopen(queryapi) as url:
        data = json.loads(url.read().decode())

# prepare empty list
list_pkg = []

# loop trough all the packages 
for dataset in data["result"]["results"]:
  
    #we are only interested in active datasets (no harvesters or showcases)      
    if (dataset["type"]=="dataset") & (dataset["state"]=="active"):
        pkg_name = dataset["name"]
        pkg_author = dataset["author"]
        pkg_title = dataset["title"]
        
        # add relevant attributes to a list
        element_list_pkg = [pkg_name, pkg_author, pkg_title]
        list_pkg.append(element_list_pkg)
        
# Convert list_pkg to dataframe for further processing (merging with mappings)
data_list = pd.DataFrame(list_pkg, columns = ['name' , 'author', 'title']) 


# PHASE 2: MAP AUTHOR OF DATASETS TO ORGANIZATIONAL UNITS
# Load the definition of all valid organizational entities */
data_org = pd.read_csv(orgcsv)
data_org["orgentity"] = data_org["DA"] + ", " + data_org["Dept"]

# Primary Mapping
data_list["orgentity"] = data_list.author.str.split(', ').str[-2] + ", " + data_list.author.str.split(', ').str[-1] 
# Left join organizational entities where the spelling is identical
data_list_org1 = pd.merge(data_list, data_org, on='orgentity', how='left')

# Secondary Mapping
data_org_map = pd.read_csv(orgmapcsv)
# Left join organizational entities with mapping list
data_list_org2 = pd.merge(data_list_org1, data_org_map, on='author', how='left')
# This results in two mapping fields: Nr and key

# Merge Nr and key - leading is the input of the manual org mapping
def org_nr(nr1, nr2):
    if pd.isnull(nr2):
        return nr1
    else:
        return nr2
data_list_org2['nrkey'] = data_list_org2.apply(lambda x: org_nr(x['Nr'],x['key']),axis=1)

# Missing mappings
data_err_miss = data_list_org2[data_list_org2["nrkey"].isnull()]

data_err_miss.to_csv(err_miss_map)

if data_err_miss.shape[0]>0:
    error = True
    message = "ERROR: " + str(data_err_miss.shape[0]) + " missing mapping(s). See " + err_miss_map
else:
    error = False
    message = "NOTE: Successfully mapped all authors"
print(message)
 

# PHASE 3: PREPARE DATA FOR REPORTING    
# Export most imprtant fields do excel for external use
data_excel_prep = data_list_org2[["name", "author", "title", "nrkey"]].copy()
data_excel_prep.rename(columns={'nrkey': 'Nr'}, inplace=True)
data_org_name = data_org[["Nr", "Organisation", "Dept", "DA"]]
data_excel_report = pd.merge(data_excel_prep, data_org_name, on='Nr', how='left')
data_excel_report.to_excel(excel_out)  

# Add department-key (first letter of nrkey) and counter to simplify further summary statistics
data_list_org2["deptkey"] = data_list_org2.nrkey.str.slice(stop=1)
data_list_org2["count"] = 1

# Aggregate results and rename and remove pivot-index for later join with pixel-positions
data_report_dept = pd.pivot_table(data_list_org2,index=["deptkey"],values=["count"],aggfunc="sum")
data_report_dept.index.names = ['Nr']
data_report_dept["type"] = "department"
data_report_dept = data_report_dept.rename_axis(None, axis=1).reset_index() 

data_report_da = pd.pivot_table(data_list_org2,index=["nrkey"],values=["count"],aggfunc="sum")
data_report_da.index.names = ['Nr']
data_report_da = data_report_da.rename_axis(None, axis=1).reset_index() 

data_pixel = data_org[["Nr", "xPixel", "yPixel"]]

data_pixel_dept = pd.merge(data_pixel, data_report_dept, on='Nr', how='left')
data_pixel_dept.rename(columns={'count': 'countDept'}, inplace=True)

data_pixel_report = pd.merge(data_pixel_dept, data_report_da, on='Nr', how='left')
data_pixel_report.rename(columns={'count': 'countDA'}, inplace=True)


# PHASE 4: CREATE REPORT
# Create report by overlaying text on an existing org-chart image
# Create report by overlaying text on an existing org-chart image
img = Image.open(image_in)
draw = ImageDraw.Draw(img)

draw.text((1500, 870), "Stand: " + today.strftime("%d.%m.%Y"), (0, 0, 0), font=font_state)

if error and show_error:
    draw.text((0, 0), message, (255, 0, 0), font=font_state)

for index, row in data_pixel_report.iterrows():
    if row["type"] == "department":
        if pd.isnull(row["countDept"]):
            text = "0"
        else:
            text = str(int(row["countDept"]))
        bbox = font_dept.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        xCoord = row["xPixel"] + box_width - text_width - padding_right_dept
        yCoord = row["yPixel"] + padding_top_dept
        draw.text((xCoord, yCoord), text, (0, 0, 0), font=font_dept)
    else:
        if pd.isnull(row["countDA"]):
            text = "0"
        else:
            text = str(int(row["countDA"]))
        bbox = font_da.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        xCoord = row["xPixel"] + box_width - text_width - padding_right_da
        yCoord = row["yPixel"] + padding_top_da
        draw.text((xCoord, yCoord), text, (0, 0, 0), font=font_da)

img.save(image_out)

