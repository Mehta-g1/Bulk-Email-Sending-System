web: python -m gunicorn Email.wsgi:application --log-file - --bind 0.0.0.0:$PORT --chdir Email
release: python Email/manage.py migrate