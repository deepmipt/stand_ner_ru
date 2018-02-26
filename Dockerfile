FROM stand/docker_cuda

VOLUME /vol
WORKDIR /app
ADD . /app

RUN pip install -r requirements.txt && \
    ./download_components.sh

EXPOSE 6004

CMD python3.6 ner_ru_api.py > /vol/ner_ru.log 2>&1