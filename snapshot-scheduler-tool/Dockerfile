FROM python:alpine

COPY requirements.txt ./
RUN apk update
RUN apk upgrade
RUN apk add --update py-pip python3-dev alpine-sdk libffi libffi-dev openssl openssl-dev gcc libc-dev make cargo autoconf automake bash
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /usr/src/app
COPY  fss-snapshot-scheduler.py .
COPY  schedule.cfg .
COPY fss-snapshot-delete.py .
COPY requirements.txt .

CMD ["python", "./fss-scheduler.py" ]
