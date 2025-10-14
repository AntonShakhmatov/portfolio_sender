FROM python:3.11-slim
WORKDIR /app
COPY . /app

# драйвер + orm
RUN pip install --no-cache-dir sqlalchemy==2.0.* pymysql==1.1.*

CMD ["python", "database.py"]
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# CMD ["python", "database.py"]
