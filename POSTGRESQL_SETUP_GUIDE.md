# PostgreSQL Setup Guide for New Developers
## Mini-Up Project

This guide is for developers who have pulled the code and need to set up PostgreSQL on their local machine.

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

**macOS (with Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Windows:**
Download and install from: https://www.postgresql.org/download/windows/

---

### Step 2: Install Python PostgreSQL Driver

Make sure you're in the project directory and virtual environment is activated:

```bash
cd /path/to/mini-up
source bin/activate  # On Windows: bin\activate
pip install psycopg2-binary
```

---

### Step 3: Create Database and User

Open PostgreSQL command line:

```bash
sudo -u postgres psql
```

Run these commands in PostgreSQL shell:

```sql
-- Create database
CREATE DATABASE miniup_db;

-- Create user with password
CREATE USER miniup_user WITH PASSWORD 'miniup_secure_password_2025';

-- Configure user settings
ALTER ROLE miniup_user SET client_encoding TO 'utf8';
ALTER ROLE miniup_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE miniup_user SET timezone TO 'Asia/Tehran';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE miniup_db TO miniup_user;
ALTER DATABASE miniup_db OWNER TO miniup_user;

-- For PostgreSQL 15+ (if needed)
\c miniup_db
GRANT ALL ON SCHEMA public TO miniup_user;

-- Exit
\q
```

---

### Step 4: Verify Database Settings

The project is already configured to use PostgreSQL. Check `miniup/settings/dev.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'miniup_db',
        'USER': 'miniup_user',
        'PASSWORD': 'miniup_secure_password_2025',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**No changes needed** - these settings are already in the code!

---

### Step 5: Run Migrations

```bash
python manage.py migrate
```

This will create all necessary tables in PostgreSQL.

---

### Step 6: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Or load existing data if available:

```bash
python manage.py loaddata data_backup_20251215_103923.json
```

---

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

---

## ✅ Verification

Test that everything is working:

```bash
# Check Django can connect
python manage.py check

# Check database connection
sudo -u postgres psql -d miniup_db -c "\dt"

# Or from Django shell
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ PostgreSQL connected!")
```

---

## 🔧 Common Issues & Solutions

### Issue 1: "peer authentication failed"

**Solution**: Edit PostgreSQL config to use password authentication.

Edit `/etc/postgresql/14/main/pg_hba.conf`:

Change this line:
```
local   all             all                                     peer
```

To:
```
local   all             all                                     md5
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

### Issue 2: "psycopg2" not found

**Solution**: Install the PostgreSQL adapter:

```bash
pip install psycopg2-binary
```

---

### Issue 3: "database does not exist"

**Solution**: Create the database again:

```bash
sudo -u postgres psql
CREATE DATABASE miniup_db;
GRANT ALL PRIVILEGES ON DATABASE miniup_db TO miniup_user;
\q
```

---

### Issue 4: "role does not exist"

**Solution**: Create the user:

```bash
sudo -u postgres psql
CREATE USER miniup_user WITH PASSWORD 'miniup_secure_password_2025';
GRANT ALL PRIVILEGES ON DATABASE miniup_db TO miniup_user;
\q
```

---

### Issue 5: PostgreSQL not running

**Ubuntu/Debian:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

**macOS:**
```bash
brew services start postgresql@14
```

**Windows:**
Start PostgreSQL from Services or pgAdmin

---

## 📋 Quick Commands Reference

| Task | Command |
|------|---------|
| Access PostgreSQL | `sudo -u postgres psql` |
| Connect to our DB | `sudo -u postgres psql -d miniup_db` |
| List databases | `\l` (in psql) |
| List tables | `\dt` (in psql) |
| Exit psql | `\q` |
| Check service status | `sudo systemctl status postgresql` |
| Restart service | `sudo systemctl restart postgresql` |

---

## 🎯 Summary

1. Install PostgreSQL
2. Install `psycopg2-binary` in virtual environment
3. Create database `miniup_db` and user `miniup_user`
4. Run `python manage.py migrate`
5. Run `python manage.py runserver`

**That's it!** You're ready to develop.

---

## 💡 Alternative: Use Existing Database Credentials

If you want to use different credentials:

1. Create your database with your preferred name/password
2. Create a `.env` file in project root:
   ```
   DB_NAME=your_db_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. Update `miniup/settings/prod.py` to use these environment variables (already configured!)

---

## 📞 Need Help?

- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Django PostgreSQL**: https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes
- **Ask the team**: Contact project maintainers

---

**Created**: December 15, 2025  
**PostgreSQL Version**: 14+ recommended  
**Python Version**: 3.10+
