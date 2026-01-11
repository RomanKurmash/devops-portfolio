FROM python:3.11-slim

WORKDIR /app

# Оптимізація Python: не створювати .pyc та не буферизувати логи
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Копіюємо та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код
COPY . .

EXPOSE 8080

# Запуск асинхронного сервера
CMD ["python", "bot.py"]