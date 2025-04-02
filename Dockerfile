# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Открываем порт для Streamlit
EXPOSE 8501

# Переменная среды для указания Streamlit запускаться на всех интерфейсах
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# Команда запуска приложения
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]