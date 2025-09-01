FROM php:8.3-cli-alpine
RUN apk add --no-cache tzdata dcron shadow \
 && useradd -u 1000 -ms /bin/sh app
USER app
WORKDIR /var/www/html