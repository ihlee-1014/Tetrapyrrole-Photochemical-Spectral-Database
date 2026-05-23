# Tetrapyrrole Photochemical Spectral Database (TPSD)  

## Database Overview  
The Tetrapyrrole Photochemical Spectral Database (TPSD) is a specialized database designed to 
organize and provide access to chemical and spectral data for tetrapyrrole compounds synthesized 
in Dr. Jonathan S. Lindsey’s laboratory.  

Tetrapyrrole macrocycles include important biological pigments such as heme and chlorophylls 
and are widely used in photochemistry, materials science, and biological research. This database 
stores spectral and chemical information for synthetic chlorophyll derivatives.  

This database was developed at Boston University as part of BF768 (Biological Database Analysis), 
Spring 2026, under the instruction of Professor Gary Benson. The student development team consists 
of Xiaohe Jin, Iris Lee, Faria Shahriar, and Jiaqi Wang.  

## Database Features
- Search compounds by compound name
- Filter compounds by solvent
- Search by absorption wavelength range
- Search by emission wavelength
- Compare spectral properties across compounds
- Download spectral data and query results

## README
To completely install this code and recreate a functional database, the following is required:  
- an internet server
- mod_wsgi
- mariadb

Our database structure has been saved in the file `db_schema.sql`. It contains `CREATE TABLE` instructions.  
On your local device, please restore it via the following code:  
```
mariadb -u your_user -p -e "CREATE DATABASE your_database_name;"
mariadb -u your_user -p your_database_name < db_schema.sql
```
All data must be uploaded manually. Please contact a team member for raw data files.  

Note that relative paths must be used if accessing files below the project folder directory. For instance:  
```
# PYTHON
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'file_folder', 'myfile.txt')
```
Similarly, relative paths must be used in URLs in the HTML template files:  
```
<form action="{{url_for('app_route1_function'}}">
<!-- where app_route1_function is the defined function under an @app.route -->
```
Please use the same coding for the URLs in AJAX requests.  

Finally, please install all packages with the following:
```
pip3 install -r requirements.txt
```

## Literature
Citation:  
Masahiko Taniguchi, David F. Bocian, Dewey Holten, Jonathan S. Lindsey, 
Beyond green with synthetic chlorophylls – Connecting structural features 
with spectral properties, Journal of Photochemistry and Photobiology C: 
Photochemistry Reviews, Volume 52, 2022, 100513, ISSN 1389-5567, 
https://doi.org/10.1016/j.jphotochemrev.2022.100513.  

Please visit the [Lindsey Lab website](https://sites.google.com/ncsu.edu/lindsey-lab/) for more information.

## Data Source
The data included in this database originate from experimental measurements and literature related 
to tetrapyrrole compounds synthesized in the laboratory of Dr. Jonathan S. Lindsey.  

Principal Investigator: Jonathan S. Lindsey  
Department of Chemistry, North Carolina State University  
Email: jslindse@ncsu.edu  
Phone: 919-515-6406  
Lab Website: https://chemistry.sciences.ncsu.edu/people/jslindse/  
