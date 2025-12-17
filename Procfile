web: gunicorn Email.wsgi --log-file - --bind 0.0.0.0:$PORT
release: python Email/manage.py migrate