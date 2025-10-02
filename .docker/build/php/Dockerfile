FROM php:8.3-apache

ENV APACHE_DOCUMENT_ROOT=/var/www/html/www

# Пакеты + модули Apache
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates git zip unzip \
    libcurl4-openssl-dev \
 && a2enmod rewrite headers \
 && rm -rf /var/lib/apt/lists/*

# PHP-расширения
RUN docker-php-ext-install pdo pdo_mysql curl \
 && docker-php-ext-install opcache

# DocumentRoot на /www
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
 && sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer