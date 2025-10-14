🚀 Быстрый старт (Docker)
Предварительные требования

Docker + Docker Compose

Заполненные ключи в конфигурации (API-ключи и доступы к БД в local.neon/env)

Сборка и запуск

sudo docker compose build
sudo docker compose up -d

Откройте приложение:
→ http://localhost

sudo docker compose exec app curl -s http://selenium:4444/status

Права для логов/кэша (нужно и локально, и на хостинге)
sudo chmod -R 0777 ./log ./temp ./www


💾 Основной сценарий использования

Зайдите на http://localhost

Загрузите резюме через форму (upload).

Данные из резюме будут сохранены в базу данных.

При запущенном проекте в Docker, парсинг и автозаполнение запускаются автоматически по крону внутри контейнеров.

Крон работает в фоне, вручную ничего запускать не нужно.

🧠 Индивидуальная обработка (embeddings контейнер)

Если хотите вручную обработать конкретный сайт/задачу:

docker exec -it portfolio-embeddings-1 sh
# внутри контейнера:
# выберите нужный сайт/задачу и запустите одноимённый .py файл, например:
python mysite.py


Имена файлов соответствуют сайтам/процессам (например, example_com.py и т.п.).

🔧 Полезные команды

Остановить:
sudo docker compose down


Пересобрать и перезапустить после изменений:
sudo docker compose build
sudo docker compose up -d


Логи основного приложения:
sudo docker compose logs -f app


Логи cron/парсинга (если в отдельном сервисе):
sudo docker compose logs -f parser
# или
sudo docker compose logs -f embeddings


Войти в основной контейнер PHP:
sudo docker compose exec app sh


🗄️ База данных

Подключение настраивается в local.neon / переменных окружения (doctrine/dbal / database.dsn и т.д.).

После старта контейнеров проверьте, что БД доступна и миграции (если есть) применены.

🧩 Конфигурация

API-ключи и прочие параметры задаются в local.neon (или в переменных окружения).
Не коммитьте реальные ключи в репозиторий.


🩺 Техническая проверка

Приложение: http://localhost
Selenium статус:
sudo docker compose exec app curl -s http://selenium:4444/status

Права на каталоги:
sudo chmod -R 0777 ./log ./temp ./www


❓Траблшутинг

403/500/“темп не пишется” → проверьте права на ./log, ./temp, ./www.

Крон “не работает” → убедитесь, что контейнеры запущены (up -d), посмотрите логи parser/embeddings.

Нет данных после загрузки резюме → проверьте логи app, подключение к БД и корректность парсера.

Selenium не отвечает → пересоберите контейнеры, проверьте сеть docker и статус по URL выше.



📦 Деплой на хостинге/локальном сервере без Docker

Настройте PHP + веб-сервер (Apache/Nginx) и БД.

Установите зависимости (composer install).

Пропишите доступы и ключи в local.neon/env.

Выдайте права:
sudo chmod -R 0777 ./log ./temp ./www

Настройте системный cron (или Supervisor) для запуска парсинга/задач по расписанию.