#!/bin/bash

if [ ! -n "${DB_HOST}" ] || [ ! -n "${REDIS_HOST}" ] || [ ! -n "${MONGODB_HOST}" ]; then
    echo "You must set the DB_HOST, REDIS_HOST and MONGODB_HOST!!!"
    exit 1
fi

inited=$(cat /initapp/inited.txt)

if [ "no" == "$inited" ]; then

: "${DEBUG:=True}"

: "${REDIS_PORT:=6379}"
: "${REDIS_PASSWD:=None}"
: "${REDIS_CELERY_DB:=0}"
: "${REDIS_ANSIBLE_DB:=2}"

: "${MONGODB_PORT:=27017}"
: "${MONGODB_USER:=admin}"
: "${MONGODB_PASSWD:=123456}"
: "${MONGODB_RECORD_DB:=records}"
: "${MONGODB_RECORD_COLL:=ops}"

: "${DB_PORT:=3306}"
: "${DB_ADMIN_USER:=root}"
: "${DB_ADMIN_PASSWD:=123456}"
: "${DB_USER:=root}"
: "${DB_PASSWD:=123456}"
: "${DB_NAME:=ops}"

: "${ANSIBLE_ROLES_PATH:=/usr/share/ansible/roles}"

: "${ZABBIX_HOST:=zabbix}"
: "${ZABBIX_PORT:=8080}"
: "${ZABBIX_API_URL:=zabbix/api_jsonrpc.php}"
: "${ZABBIX_GRAPH_URL:=zabbix/chart2.php}"
: "${ZABBIX_LOGIN_URL:=zabbix/index.php}"
: "${ZABBIX_USER:=admin}"
: "${ZABBIX_PASSWD:=123456}"

: "${CUACD_HOST:=cuacd}"
: "${CUACD_PORT:=4822}"

: "${SMTP_HOST:=smtp.163.com}"
: "${SMTP_PORT:=25}"
: "${SMTP_USER:=ops@163.com}"
: "${SMTP_PASSWD:=123456}"

: "${ADMIN_USER:=admin}"
: "${ADMIN_EMAIL:=ops@163.com}"
: "${ADMIN_PASSWD:=ChangeMe123}"

cat > /app/conf/ops.ini <<EOF
[global]
debug = ${DEBUG}

[redis]
host = ${REDIS_HOST}
port = ${REDIS_PORT}
password = ${REDIS_PASSWD}
celery_db = ${REDIS_CELERY_DB}
ansible_db = ${REDIS_ANSIBLE_DB}

[mongodb]
host = ${MONGODB_HOST}
port = ${MONGODB_PORT}
user = ${MONGODB_USER}
password = ${MONGODB_PASSWD}
record_db = ${MONGODB_RECORD_DB}
record_coll = ${MONGODB_RECORD_COLL}

[db]
host = ${DB_HOST}
port = ${DB_PORT}
user = ${DB_USER}
password = ${DB_PASSWD}
name = ${DB_NAME}
admin_user = ${DB_ADMIN_USER}
admin_password = ${DB_ADMIN_PASSWD}

[ansible]
ansible_role_path = ${ANSIBLE_ROLES_PATH}

[zabbix]
host = ${ZABBIX_HOST}
port = ${ZABBIX_PORT}
api_url = ${ZABBIX_API_URL}
graph_url = ${ZABBIX_GRAPH_URL}
login_url = ${ZABBIX_LOGIN_URL}
username = ${ZABBIX_USER}
password = ${ZABBIX_PASSWD}

[cuacd]
host = ${CUACD_HOST}
port = ${CUACD_PORT}

[email]
smtp_host = ${SMTP_HOST}
smtp_port = ${SMTP_PORT}
smtp_user = ${SMTP_USER}
smtp_passwd = ${SMTP_PASSWD}
EOF

sleep 30;
mysql -u${DB_ADMIN_USER} -p${DB_ADMIN_PASSWD} -h ${DB_HOST} -P ${DB_PORT} -e "CREATE USER '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWD}';"
mysql -u${DB_ADMIN_USER} -p${DB_ADMIN_PASSWD} -h ${DB_HOST} -P ${DB_PORT} -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;"
mysql -u${DB_ADMIN_USER} -p${DB_ADMIN_PASSWD} -h ${DB_HOST} -P ${DB_PORT} -e "grant all privileges on ${DB_NAME}.* to ${DB_USER}@'%' identified by '${DB_PASSWD}';"
python manage.py makemigrations users assets dbmanager fort plan projs task wiki
python manage.py migrate
echo "python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('${ADMIN_USER}', '${ADMIN_EMAIL}', '${ADMIN_PASSWD}')\"" > /tmp/create_superuser.sh
/bin/bash /tmp/create_superuser.sh
echo "yes" > /initapp/inited.txt
fi

export CELERY_BIN="\/usr\/local\/bin\/celery" && sed -i 's/^CELERY_BIN=.*$/CELERY_BIN="'$CELERY_BIN'"/g' /etc/default/celeryd
export CELERYD_CHDIR="\/app" && sed -i 's/^CELERYD_CHDIR=.*$/CELERYD_CHDIR="'$CELERYD_CHDIR'"/g' /etc/default/celeryd
export C_FORCE_ROOT="true"
/etc/init.d/celeryd start
/etc/init.d/celerybeat start

python manage.py runserver 0.0.0.0:8000
