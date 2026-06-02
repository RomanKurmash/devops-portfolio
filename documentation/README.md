# DevOps & SecOps Portfolio: Monitoring, Logging & AI Automation

Цей проєкт демонструє навички побудови інфраструктури для моніторингу, логування, автоматизованого виявлення загроз за допомогою штучного інтелекту (LLM) та автоматизації CI/CD.

---

## 🛠 Технологічний стек

* **Оркестрація та контейнеризація:** Docker, Docker Compose.
* **Моніторинг:** Prometheus, MySQL Exporter, Node Exporter, Nginx Exporter.
* **Логування:** Grafana Loki, Promtail.
* **SecOps AI Engine:** Локальна LLM Llama-3 (через Ollama з апаратним прискоренням GPU).
* **AI-Adapter (Python):** Сканер логів у реальному часі для виявлення 10 категорій загроз.
* **Telegram Bot (Python):** Сповіщення про інциденти та інтелектуальне збагачення (Alert Enrichment) причин аварій через LLM.
* **Документація та звітність:** Автоматична генерація PDF-документів за допомогою Python (`markdown`, `xhtml2pdf`).
* **CI/CD:** Jenkins (автоматизація збірки, деплою, перевірки працездатності та збірки документації).

---

## 🏗 Архітектура проєкту

Проєкт складається з наступних рівнів:
1. **Infrastructure Layer:** Docker-контейнери додатків (WordPress, MySQL, Nginx Proxy).
2. **Monitoring & Logging Layer:** Збір метрик (Prometheus) та збір логів (Loki + Promtail).
3. **SecOps AI-Scanner Layer:** AI-адаптер періодично сканує Loki за допомогою LogQL, аналізує аномалії через Llama-3 на GPU та пушить критичні загрози (`risk_score >= 7`) в Alertmanager.
4. **Alerting & Enrichment Layer:** Alertmanager направляє алерти на Telegram-бот. Бот автоматично витягує останні логи збійного контейнера з Loki, просить LLM знайти точну причину та надсилає детальний звіт користувачу.

---

## 🚀 Як запустити

1. Клонуйте репозиторій:
   `git clone https://github.com/RomanKurmash/devops-portfolio.git`
2. Налаштуйте змінні середовища у файлі `.env` (токен Telegram-бота, Chat ID тощо).
3. Розгорніть інфраструктуру за допомогою Jenkins Pipeline (проєкт містить налаштований `Jenkinsfile`) або запустіть локально:
   ```bash
   docker compose -f app-infrastructure/docker-compose.apps.yml up -d
   docker compose -f app-infrastructure/docker-compose.monitoring.yml up -d
   ```

---

## 📊 Автоматичний експорт документації в PDF

Для генерації звітності та дипломної документації реалізовано автоматичний експорт:
* Скрипт `scripts/export_pdf.py` зчитує всі Markdown-файли, автоматично завантажує та вбудовує Mermaid-діаграми у вигляді графічних PNG, застосовує стилі та експортує у PDF.
* Запуск скрипту:
  ```bash
  python3 scripts/export_pdf.py
  ```
