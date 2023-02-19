#* ______ DB Migrations ______ *#

# make migrations 
python manage.py makemigrations pds
python manage.py makemigrations sch
python manage.py makemigrations 

# perform migration
python manage.py migrate 



