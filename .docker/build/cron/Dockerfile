FROM php:8.3-cli-alpine

# В Alpine cron уже есть в busybox; ставим только tzdata и bash (по желанию)
RUN apk add --no-cache tzdata bash

RUN docker-php-ext-install pdo_mysql

ENV TZ=Europe/Prague

WORKDIR /var/www/html
# COPY не обязателен, т.к. ты монтируешь volume в compose
# COPY . /var/www/html