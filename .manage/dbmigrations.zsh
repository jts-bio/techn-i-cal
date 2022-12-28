#* ______ DB Migrations ______ *#

python manage.py makemigrations pds
python manage.py makemigrations sch
python manage.py makemigrations flow

python manage.py migrate 


