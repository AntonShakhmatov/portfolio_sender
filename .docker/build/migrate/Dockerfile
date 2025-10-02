# .docker/build/migrate/Dockerfile
# 1) vendor stage: ставим PHP-зависимости
FROM composer:2 AS vendor
WORKDIR /var/www/html
COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist --no-progress --no-interaction

# 2) runtime stage: php-cli + pdo_mysql
FROM php:8.3-cli
RUN docker-php-ext-install pdo pdo_mysql
WORKDIR /var/www/html

# Копируем всё приложение
COPY . .

# Подмешиваем vendor из первой стадии
COPY --from=vendor /var/www/html/vendor ./vendor

ENTRYPOINT ["php"]
