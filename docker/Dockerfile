FROM python:3.12-slim-bullseye

RUN pip install --upgrade pip && \
    pip install pipenv

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --dev --system
