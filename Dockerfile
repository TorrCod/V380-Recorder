FROM python:3.11.0

WORKDIR /app/

ENV VIRTUAL_ENV = /app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get -y update
RUN apt-get install ffmpeg libsm6 libxext6  -y

ADD main.py .
ADD cloudstorage.py .
ADD requirements.txt .

RUN pip install -r requirements.txt

CMD ["python","/app/main.py"]