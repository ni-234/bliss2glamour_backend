FROM python:3.10-slim

LABEL maintainer="Nisansa Pasandi <ranthatigenisansa2021@gmail.com>"

ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /code/app

COPY ./static /code/static

COPY ./ui /code/ui

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "curl" , "--fail", "http://127.0.0.1:80/api/health" ]

EXPOSE 80

ENTRYPOINT ["fastapi", "run", "app/main.py"]
CMD ["--port", "80"]
