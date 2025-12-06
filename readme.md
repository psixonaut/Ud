# 🚗 CRM Автосалона (Django + PostgreSQL)

Веб-приложение для управления автосалоном: учет автомобилей, продажи, тест-драйвы и сотрудники.

## 📋 Требования

*   Python 3.10+
*   PostgreSQL 14+

## 🚀 Установка и запуск

### 1. Клонирование и виртуальное окружение

Склонируйте репозиторий и создайте виртуальное окружение:

```bash
# Клонирование (если еще не сделали)
git clone <ссылка_на_ваш_репозиторий>
cd <папка_проекта>

# Создание виртуального окружения
python -m venv venv

# Активация:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка Базы Данных (Важно!)

Так как проект использует существующую схему БД с триггерами и `managed=False`, **стандартные миграции Django не создадут таблицы автосалона**.

1.  Создайте пустую базу данных в PostgreSQL (например, `auto_shop_db`).
2.  Разверните в неё дамп структуры (файл `backup.sql` или `dump.sql`, который должен лежать в корне проекта).

```bash
# Если вы используете psql в терминале:
psql -U postgres -d auto_shop_db -f backup.sql
```
*(Если файла backup.sql нет, попросите его у разработчика или сделайте экспорт из рабочей базы).*

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта (рядом с `manage.py`) и укажите настройки подключения:

```env
SECRET_KEY=ваш_секретный_ключ
DEBUG=True

# Настройки БД
DB_NAME=auto_shop_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль_от_postgres
DB_HOST=localhost
DB_PORT=5432
```

### 5. Подготовка Django

Создайте системные таблицы Django (админка, пользователи) и суперпользователя:

```bash
# Создаем таблицы Django (auth, sessions и т.д.)
python manage.py migrate

# Если возникнет ошибка "Table already exists", используйте:
# python manage.py migrate --fake-initial

# Создаем администратора для входа
python manage.py createsuperuser
```

### 6. Запуск

```bash
python manage.py runserver
```

Перейдите в браузере по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🛠 Полезные команды

**Если сбились счетчики ID (ошибка Duplicate Key):**
Запустите скрипт починки последовательностей через консоль:
```bash
python manage.py shell
```
*(Вставьте код скрипта синхронизации sequences)*

**Сделать дамп базы (для сохранения):**
```bash
pg_dump -U postgres -h localhost -p 5432 auto_shop_db > backup.sql
```