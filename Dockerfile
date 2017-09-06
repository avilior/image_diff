FROM alior/alpine-py36-opencv32:latest

MAINTAINER Avi Lior <avi@lior.org>

RUN apk update \
    && apk add --no-cache freetype

# developement stuff that can be deleted
RUN apk add --no-cache --virtual .build-deps \
        build-base \
        clang \
        clang-dev \
        cmake \
        git \
        wget \
        unzip \
        libffi-dev \
        freetype-dev \
        openssl-dev

# RUN apk add --no-cache libffi-dev  python3-dev py3-pip
# RUN pip install cffi

ADD ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

RUN apk del .build-deps

# get the application into the container
ADD /compare_image /app/compare_image

# expose the port
EXPOSE 80

WORKDIR /app/compare_image

ENTRYPOINT ["python", "main.py"]
CMD ["--host", "0.0.0.0", "--port", "80", "--upload", "/tmp/uploads"]


