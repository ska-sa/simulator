FROM radioastro/meqtrees
RUN apt-get install -y time wsclean

ADD . /code
ADD run.sh /
WORKDIR /code

RUN mkdir /input /output

cmd /run.sh
