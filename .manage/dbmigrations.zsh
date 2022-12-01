#*=*=*=*= DB Migrations =*=*=*=*#

python manage.py makemigrations pds
python manage.py makemigrations sch
python manage.py makemigrations flow

python3 manage.py migrate 

#*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*#