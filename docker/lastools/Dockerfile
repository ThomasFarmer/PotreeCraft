FROM ubuntu:20.04
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y wine wget unzip \
    # For some reason, we need a separate step for adding a wine32 architecture
    && dpkg --add-architecture i386 \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y wine32 \
    && wget https://lastools.github.io/download/LAStools.zip \
    && unzip LAStools.zip \
    # Run one program to configure wine
    && wine LAStools/bin/las2las -h
COPY entrypoint.sh entrypoint.sh
WORKDIR /lastools
ENTRYPOINT ["/./entrypoint.sh"]


# docker run -v "$(pwd):/lastools" lastools las2las -i input.laz -o output.las
# sudo docker run -it --entrypoint /bin/bash thomasfarmer/lastoolsindocker
# sudo docker run --mount type=bind,source=$PWD,destination=/lastools thomasfarmer/lastoolsindocker blast2dem -i ./roadsection.las -o output.asc -step 2
