FROM python:3.9-alpine

WORKDIR /app

# Копіюємо код бота всередину образу
COPY . /app

# Встановлюємо залежності одразу при збірці
RUN pip install flask requests

# Запускаємо
CMD ["python", "bot.py"]