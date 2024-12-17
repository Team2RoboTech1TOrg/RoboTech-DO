FROM kubeflownotebookswg/jupyter-pytorch-cuda-full:v1.9.2

# Копируем файл с зависимостями
COPY requirements.txt /requirements.txt

# Устанавливаем библиотеки из requirements.txt в системное окружение
RUN pip install --no-cache-dir -r /requirements.txt

