## 🧠 English Version

# INFLUENCE.HUB Telegram Bot

A modular Telegram bot built with **Aiogram 3**, designed for influencer engagement, task tracking, gamification (coins, levels, badges), and mentorship flows.

---

### 🚀 Features

* **Welcome & Role Selection** – dynamic start flow with role-based onboarding.
* **Main Menu** – easy navigation with sections: Profile, Tasks, Rating, Mentorship, Calendar, Courses, Help.
* **Profile System**

  * Shows user’s level, coins, progress bar, badges, rating position.
  * `/whoime` command – quick profile info shortcut.
  * History of completed tasks with difficulty filters (🟢 / 🟡 / 🔴).
* **Task Catalog**

  * Tasks grouped by difficulty and reward.
  * Accept, complete, and submit with deadlines and instructions.
* **Activity History**

  * Split into Active / Submitted / Done groups.
  * Pagination and difficulty filter with emoji indicators.
* **Gamification**

  * Level system based on total coins.
  * Progress bar between levels.
  * Badges based on milestones.
* **Admin Panel**

  * Create and publish tasks.
  * Manage mentors and assign coins.
  * View influencer activity analytics.
* **Webhooks ready**

  * Supports PythonAnywhere or similar hosting for 24/7 uptime.

---

### ⚙️ Tech Stack

* Python 3.11+
* Aiogram 3.x
* SQLAlchemy
* SQLite (default)
* dotenv for environment config
* Optional: Flask app for webhook deployment

---

### 🧩 Project Structure

```
bot/
├── handlers/           # Main conversation logic
│   ├── start.py        # Welcome flow
│   ├── menu.py         # Main menu
│   ├── profile.py      # Profile, levels, badges
│   ├── task/           # Catalog and submissions
│   └── admin/          # Admin panel
├── services/           # DB + business logic
│   ├── users.py
│   ├── tasks.py
│   ├── levels.py
│   └── badges.py
├── storage/            # DB models & connection
├── keyboards/          # Inline & reply keyboards
├── states/             # FSM states
├── middlewares/        # Logging, filters
└── main.py             # Bot entry point
```

---

### 🧰 Commands

| Command   | Description                   |
| --------- | ----------------------------- |
| `/start`  | Start or restart bot          |
| `/whoime` | Show user profile summary     |
| `/admin`  | Open admin panel (admin only) |
| `/help`   | FAQ & support info            |

---

### 🧾 Environment (.env)

```
BOT_TOKEN=123456:ABC-DEF...
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite:///bot.db
WEBHOOK_URL=https://your-pythonanywhere-app/webhook/<SECRET>
```

---

### 💡 Deployment (PythonAnywhere)

1. Clone the repo to `/home/<user>/tgbot_for-ithub/`
2. Create venv → `python3.10 -m venv venv && source venv/bin/activate`
3. Install deps → `pip install -r requirements.txt`
4. Configure `.env` file
5. Set webhook:

   ```bash
   python -m tools.set_webhook
   ```
6. Add a web app with Flask runner → `webapp.py`

---

## 🇷🇺 Русская версия

# INFLUENCE.HUB — Telegram-бот

Модульный Telegram-бот на **Aiogram 3**, разработанный для вовлечения инфлюенсеров, отслеживания заданий, геймификации и менторства.

---

### 🚀 Основной функционал

* **Приветствие и выбор роли** — гибкое онбординг-окно для участников.
* **Главное меню** — быстрый доступ к разделам: Профиль, Задания, Рейтинг, Менторство, Календарь, Курсы, Помощь.
* **Профиль**

  * Уровни, прогресс-бар, монеты, бейджи и позиция в рейтинге.
  * Команда `/whoime` — показать профиль в любой момент.
  * История активности с фильтрами по сложности (🟢 / 🟡 / 🔴).
* **Каталог заданий**

  * Задания по категориям сложности и награде.
  * Кнопки «Взять», «Подробнее», «Сдать задание».
* **История активности**

  * Разделена на: Активные / На проверке / Завершённые.
  * Поддерживает пагинацию и фильтр сложности.
* **Геймификация**

  * Система уровней и наград за прогресс.
  * Автоматические бейджи за достижения.
* **Админ-панель**

  * Создание заданий, начисление баллов, аналитика.
* **Веб-хуки**

  * Готов для размещения на PythonAnywhere (работает 24/7).

---

### ⚙️ Технологии

* Python 3.11+
* Aiogram 3.x
* SQLAlchemy
* SQLite
* dotenv
* Flask (для вебхуков)

---

### 🧰 Основные команды

| Команда   | Описание                                 |
| --------- | ---------------------------------------- |
| `/start`  | Запустить/перезапустить бота             |
| `/whoime` | Показать профиль                         |
| `/admin`  | Вход в админ-панель (только для админов) |
| `/help`   | Помощь и контакты                        |

---

### 💾 Файл окружения (.env)

```
BOT_TOKEN=123456:ABC-DEF...
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite:///bot.db
WEBHOOK_URL=https://your-pythonanywhere-app/webhook/<SECRET>
```

---

Хочешь, я сразу вставлю этот README.md в проект (заменю старый) и сделаем коммит + пуш в main?
