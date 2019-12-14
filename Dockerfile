FROM python:3.7.5-slim-stretch

RUN apt-get update && apt-get upgrade -y

WORKDIR /sources
ADD ./requirements.txt /sources/requirements.txt
RUN pip install -r /sources/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/sources/src"

ADD . /sources

CMD ["python", "src/polar/proxy/proxy_service.py"]
