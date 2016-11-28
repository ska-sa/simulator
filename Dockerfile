FROM kernsuite/casa:4.7

RUN docker-apt-install \
        time \
        wsclean \
        python-pip \
        python-casacore \
        python-numpy \
        python-pyfits \
        python-owlcat \
        python-kittens \
        python-scipy \
        python-astlib \
        python-tigger \
        python-pyxis \
        python-pymoresane \
        meqtrees 

# we need to get simms from pypi since it depends on the unpackaged casa
RUN pip install simms 

ADD src /code

RUN mkdir /input /output

ENV MEQTREES_CATTERY_PATH /usr/lib/python2.7/dist-packages/Cattery

ADD kliko.yml /kliko.yml
ADD src/run.sh /kliko

WORKDIR /code
CMD /kliko
