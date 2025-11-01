## 🇬🇧 **InfluenceHub Telegram Bot**

A Telegram bot for managing influencer activities, gamified tasks, mentoring, and leaderboard inside the **InfluenceHub** ecosystem.

---

### ✨ Features

* **Welcome flow** — onboarding and role selection
* **Main menu** — profile, tasks catalog, ratings, mentoring, calendar, and learning modules
* **Task system** — dynamic task catalog with difficulty levels, acceptance and submission flow
* **Profile & Activity history** — coins, rating, badges, and history of completed tasks
* **Admin panel** — review user submissions, approve/reject tasks, automatically assign coins
* **AI-based segmentation (future)** — personalized task and content recommendations

---

### 🧩 Tech Stack

* **Python 3.11+**
* **[Aiogram 3](https://docs.aiogram.dev/en/latest/)**
* **SQLAlchemy** for local data storage
* **Flask** for webhook endpoint (PythonAnywhere-compatible)
* **dotenv** for configuration management

---

### ⚙️ Installation (Local)

```bash
git clone https://github.com/KMM05XAK20/tgbot_for-ithub.git
cd tgbot_for-ithub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root:

```
BOT_TOKEN=1234567890:ABCDEF_your_token
ADMIN_IDS=123456789
PA_BASE_URL=https://yourname.pythonanywhere.com
WEBHOOK_SECRET=mysupersecret
```

Run locally:

```bash
python -m bot.main
```

---

### ☁️ Deploy to PythonAnywhere (Webhook)

1. Clone repo and set up virtual environment on PythonAnywhere.
2. Add environment variables in **Web → Environment Variables**.
3. Add Flask web app with WSGI pointing to `webapp.py`:

   ```python
   import sys, os
   project_home = os.path.expanduser('~/tgbot_for-ithub')
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   from webapp import app as application
   ```
4. Run once:

   ```bash
   python -m tools.set_webhook
   ```
5. Reload the web app — done! Bot runs 24/7.

---

### 🧰 Development

* Start polling locally for testing
* Use feature branches (`feat/...`) for new flows
* Merge into `main` before deployment

---

### 🛠️ Admin Commands

* `/admin` — open admin panel
* `admin:view:<id>` — view specific submission
* Approve/reject buttons automatically send user notifications and update coins

---

### 📜 License

MIT — open for educational and non-commercial use.

---

---

## 🇷🇺 **InfluenceHub Telegram Бот**

Телеграм-бот для управления активностями инфлюенсеров, выполнения заданий, менторства и рейтингов в экосистеме **InfluenceHub**.

---

### ✨ Возможности

* **Приветственный поток** — onboarding и выбор роли
* **Главное меню** — профиль, каталог заданий, рейтинг, менторство, календарь, прокачка
* **Система заданий** — уровни сложности, взятие и сдача заданий
* **Профиль и история активности** — баллы, место в рейтинге, бейджи
* **Админ-панель** — проверка и подтверждение заданий, начисление монет
* **AI-сегментация (план)** — персонализированные задания и контент

---

### 🧩 Технологии

* Python 3.11+
* Aiogram 3
* SQLAlchemy
* Flask (вебхуки)
* python-dotenv

---

### ⚙️ Установка локально

```bash
git clone https://github.com/KMM05XAK20/tgbot_for-ithub.git
cd tgbot_for-ithub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создай `.env` в корне проекта:

```
BOT_TOKEN=твой_токен_бота
ADMIN_IDS=твой_ID
PA_BASE_URL=https://kmm005.pythonanywhere.com
WEBHOOK_SECRET=mysupersecret
```

Запуск:

```bash
python -m bot.main
```

---

### ☁️ Развёртывание на PythonAnywhere

1. Склонируй репозиторий.
2. Создай виртуальное окружение, установи зависимости.
3. Добавь переменные окружения в разделе **Web → Environment Variables**.
4. В WSGI-файл впиши:

   ```python
   import sys, os
   project_home = os.path.expanduser('~/tgbot_for-ithub')
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   from webapp import app as application
   ```
5. Выполни:

   ```bash
   python -m tools.set_webhook
   ```
6. Нажми **Reload** — бот начнёт работать 24/7.

---

### 🧰 Для разработчиков

* Запускай локально через polling.
* Разрабатывай в ветках `feat/...`.
* Мерджи в `main` перед деплоем.

---

### 🛠️ Команды администратора

* `/admin` — вход в панель
* `admin:view:<id>` — открыть заявку
* Кнопки ✅ / ❌ управляют статусом задания и уведомляют пользователя
