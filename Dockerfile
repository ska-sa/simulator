FROM radioastro/meqtrees
RUN apt-get install -y time wsclean

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

ADD src /code
RUN ln -s /code/run.sh /run.sh

RUN mkdir /input /output

RUN apt-get install -qy linux-tools-common linux-tools-generic-lts-trusty linux-tools-3.16.0-33-generic bc

WORKDIR /code
cmd /run.sh



