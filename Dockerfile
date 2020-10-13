FROM python:3.8-slim as pipenv

WORKDIR /usr/src/app

RUN pip install pipenv

COPY ./Pipfile* ./

RUN pipenv lock --requirements > requirements.txt

FROM python:3.8-slim

WORKDIR /usr/src/app

RUN mkdir /data

COPY --from=pipenv /usr/src/app/requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python" ]
CMD ["./main.py"]