FROM radioastro/meqtrees
RUN apt-get install -y time wsclean

ADD . /code
WORKDIR /code

RUN mkdir /results
cmd ./runsim.sh
