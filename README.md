CLONE REPO
git clone https://github.com/TorrCod/V380-Recorder.git

BUILD DOCKER
docker build -t recorder_v2 .

RUN DOCKER
docker run -it recorder_v2 