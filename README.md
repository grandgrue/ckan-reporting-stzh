# ckan-reporting-stzh
Creates a list of datasets per organizational unit based on the ckan-api and visualizes it.
Download this repository and run execute ckan-reporting-stzh.py to create the report.

## Input

The script uses the CKAN API of https://data.stadt-zuerich.ch to retrieve a list of all active datasets in the data catalog.

## Mapping

### Primary Mapping
For the primary mapping the file organizations.csv is used. If the author of a dataset is spelled the same way as the organizational unit, it maps the unique id to it.

The structure of organizations.csv is as follows

| Nr  | Organisation | Dept | DA | xPixel | yPixel |
| :-- | :----------- | :--- | :- | :----- | :----- |
| A   | Stadt Zürich | Präsidialdepartement | Alle | 12 | 282 |
| A01 | Stadt Zürich | Präsidialdepartement | Departementssekretariat PRD | 12 | 333 |
| A02 | Stadt Zürich | Präsidialdepartement | Bevölkerungsamt | 12 | 385 |
| A03 | Stadt Zürich | Präsidialdepartement | Statistik Stadt Zürich | 12 | 436 |

The file organizations.csv shall NOT be changed if a mapping is missing. It represents the organizational structure of the City of Zurich and is used to position the output on the image. 

### Secondary Mapping
For the secondary mapping the file org-mapping.csv is used. 
Please add any missing mapping to this file. The "key" values need to match with an "Nr" value in organizations.csv.

The structure of org-mapping.csv is as follows

| key | author |
| :-- | :----- |
| A03 | "Statistik Stadt Zürich, Gebäude- und Wohnungsregister" |
| S03 | "Stadtkanzlei, Stadt Uster" |

### Missing Mappings
A missing mapping is indicated with an error-message and the corresponding dataset is listed in a file called error_missing-mapping.csv. 
In that case, create a new entry in org-mapping.csv and rerun the script. You can use the mode=3 switch (to be modified in the code of ckan-reporting-stzh.py) to skip the data retrieval part.

Please create a pull request for your changes to org-mapping.csv.

## Output

A new report image named "Report OGD Datensätze nach Departement und Dienstabteilung.png" is created based on the template image stzh-org-template.png. The sum of datasets per organizational unit is overlayed. The x and y pixel position for the overlay can be found in organizations.csv

Additionally the script produces a simple excel file called "Report OGD Datensätze nach Organisationseinheit.xlsx" with all the datasets and the mapped organizational units.



