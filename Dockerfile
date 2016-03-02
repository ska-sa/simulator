FROM radioastro/casa:4.2

RUN apt-get update &&  \
    apt-get install -y \
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
        meqtrees \
    && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install pymoresane simms 

ADD src /code

RUN mkdir /input /output

ENV MEQTREES_CATTERY_PATH /usr/lib/python2.7/dist-packages/Cattery

ADD kliko.yml /

WORKDIR /code
CMD /code/run.sh
