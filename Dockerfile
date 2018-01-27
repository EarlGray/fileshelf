FROM python:3.6-alpine
LABEL maintainer="dmytrish@gmail.com"

ADD fileshelf /usr/app/fileshelf/
ADD static /usr/app/static
ADD tmpl /usr/app/tmpl/
ADD index.py /usr/app/
ADD requirements.txt /usr/app/

WORKDIR /usr/app
RUN pip install -r requirements.txt
RUN ln -s /storage

ENTRYPOINT python index.py -c /etc/fileshelf.conf
VOLUME /storage
VOLUME /etc/fileshelf.conf
EXPOSE 8021:8021/tcp
