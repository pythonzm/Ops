FROM python:3.6-slim-stretch

WORKDIR /app

COPY sources.list /etc/apt/sources.list
COPY requirements.txt ./
RUN apt update \
 && apt install -y default-libmysqlclient-dev gcc python-dev libsasl2-dev git sshpass mariadb-client \
 && pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple \
 && rm -rf /var/lib/apt/lists/*

COPY . .
RUN cp conf/celeryd.conf /etc/default/celeryd \
    && cp conf/celeryd.server /etc/init.d/celeryd \
    && cp conf/celerybeat.server /etc/init.d/celerybeat \
    && cp conf/get_mem.py /usr/local/lib/python3.6/site-packages/ansible \
    && chmod +x /etc/init.d/celeryd /etc/init.d/celerybeat /usr/local/lib/python3.6/site-packages/ansible/get_mem.py /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
