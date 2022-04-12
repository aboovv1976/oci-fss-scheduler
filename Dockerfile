FROM python:alpine

COPY requirements.txt ./
RUN apk update
RUN apk upgrade
RUN apk add --update py-pip python3-dev alpine-sdk libffi libffi-dev openssl openssl-dev gcc libc-dev make cargo autoconf automake bash
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /usr/src/app
COPY  fss-scheduler.py .
COPY  oci_api.py .
COPY  schedule.cfg .

CMD ["/bin/echo", "Hello, container for oci ckpt scheduler" ]

