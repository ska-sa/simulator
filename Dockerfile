FROM radioastro/meqtrees
RUN apt-get install -y time git subversion policycoreutils wsclean
ADD casarc /root/.casarc

ADD . /code
WORKDIR /code
RUN svn co https://svn.cv.nrao.edu/svn/casa-data/distro/geodetic
RUN git clone -b devel https://github.com/SpheMakh/pyxis
RUN tar -zxvf casapy-42.2.30986-1-64b.tar.gz
RUN mkdir /results
cmd ./runsim.sh
