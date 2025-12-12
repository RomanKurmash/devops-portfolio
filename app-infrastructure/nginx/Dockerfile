FROM nginx:alpine

# Видаляємо стандартний конфіг, щоб не заважав
RUN rm /etc/nginx/conf.d/default.conf

# Копіюємо головний файл конфігурації
# (Припускаємо, що nginx.conf лежить в тій же папці, що і цей Dockerfile)
COPY nginx.conf /etc/nginx/nginx.conf

# Копіюємо папку з додатковими конфігами (якщо вона є)
COPY conf.d/ /etc/nginx/conf.d/

# Щодо SSL: якщо сертифікати вже є в репозиторії, розкоментуй рядок нижче.
# Якщо ні (ти їх генеруєш динамічно), то залишимо це через volume в compose.
# COPY ssl/ /etc/nginx/ssl/