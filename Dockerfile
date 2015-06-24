FROM radioastro/meqtrees
RUN apt-get update &&  apt-get install -y \
    time \
    wsclean \
    git \
    casacore \
    python-pymoresane

pip install simms
RUN mkdir -p /code/depends
RUN git clone https://github.com/ska-sa/pyxis /code/depends/pyxis

RUN cd /code/depends/pyxis && python setup.py install

ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/casapy

ENV USER root

ADD casapy-42.2.30986-1-64b.tar.gz /opt/
RUN ln -s /opt/casapy-42.2.30986-1-64b /opt/casapy

RUN apt-get update && apt-get -qy install \
    libglib2.0-0 \
    libfreetype6 \
    libsm6 \
    libxi6 \
    libxrender1 \
    libxrandr2 \
    libxfixes3 \
    libxcursor1 \
    libxinerama1 \
    libfontconfig1 \
    libkrb5-3 \
    libgssapi-krb5-2

ADD input /code
ADD src /code
RUN ln -s /code/run.sh /run.sh

RUN mkdir /input /output

WORKDIR /code
cmd /run.sh
