FROM python:3.12.3-alpine3.18

WORKDIR /app

RUN apk update && apk add openssh-client

COPY . .

RUN \
 apk add --no-cache python3 postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

CMD ["python3", "bot.py"]
