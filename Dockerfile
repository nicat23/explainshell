# Dockerfile
ARG CODE_VERSION=latest
FROM python:3.13-alpine  

RUN addgroup -S appuser && adduser -S appuser -G appuser

RUN apk add --no-cache make curl perl man-db

WORKDIR /opt/webapp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN touch /opt/webapp/application.log && chown -R appuser:appuser /opt/webapp

USER appuser

HEALTHCHECK CMD curl -f http://localhost:5000/ || exit 1

EXPOSE 5000
CMD ["make", "serve"]
