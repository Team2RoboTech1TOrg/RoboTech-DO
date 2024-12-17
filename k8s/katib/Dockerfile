FROM python:3.8-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Копирование все файлы проекта
COPY train.py /app/train.py

# Установка необходимых пакетов
RUN pip install --no-cache-dir numpy

# Запуск программы
CMD ["python3", "train.py"]
