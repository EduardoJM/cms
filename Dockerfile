FROM python:3.13

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y \
    python3-dev \
    libgdal-dev \
    default-libmysqlclient-dev

COPY ./pyproject.toml /app/pyproject.toml
RUN pip install .

COPY ./app /app
