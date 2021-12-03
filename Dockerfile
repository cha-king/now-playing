FROM python

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY ./now-playing ./now-playing

CMD ["uvicorn", "now-playing:app", "--host=0.0.0.0"]

EXPOSE 8000
