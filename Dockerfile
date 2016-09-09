FROM python:2.7

MAINTAINER Seb Bacon version: 0.1
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements /tmp/requirements/
RUN pip install -r /tmp/requirements/production.txt && rm -rf /tmp/requirements
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - && apt-get install -y  nodejs binutils libproj-dev gdal-bin libgeoip1 libgeos-c1 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /npm
ADD openprescribing/media/js /npm/
RUN ls -l /npm/
# Install npm outside the location where we'll eventually install the
# software, for symlinking back in as part of our docker-compose run
# command. This allows us to do all the install stuff in the image,
# rather than at runtime.
RUN cd /npm && npm install -g browserify && npm install -g jshint && npm install
