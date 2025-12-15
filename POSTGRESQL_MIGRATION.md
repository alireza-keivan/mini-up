# PostgreSQL Migration - Mini-Up Project

## ✅ Migration Complete

The project has been successfully migrated from SQLite to PostgreSQL.

---

## 📊 Database Information

- **Database Name**: `miniup_db`
- **Database User**: `miniup_user`
- **Database Password**: `miniup_secure_password_2025`
- **Host**: `localhost`
- **Port**: `5432`
- **Connection Pooling**: Enabled (CONN_MAX_AGE: 600 seconds)

---

## 🔧 What Was Done

### 1. **PostgreSQL Installation**
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

### 2. **Python PostgreSQL Driver**
```bash
pip install psycopg2-binary
```

### 3. **Database & User Creation**
```bash
sudo -u postgres psql
CREATE DATABASE miniup_db;
CREATE USER miniup_user WITH PASSWORD 'miniup_secure_password_2025';
ALTER ROLE miniup_user SET client_encoding TO 'utf8';
ALTER ROLE miniup_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE miniup_user SET timezone TO 'Asia/Tehran';
GRANT ALL PRIVILEGES ON DATABASE miniup_db TO miniup_user;
ALTER DATABASE miniup_db OWNER TO miniup_user;
```

### 4. **Django Settings Updated**

**Development Settings** (`miniup/settings/dev.py`):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'miniup_db',
        'USER': 'miniup_user',
        'PASSWORD': 'miniup_secure_password_2025',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

**Production Settings** (`miniup/settings/prod.py`):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='miniup_db'),
        'USER': env('DB_USER', default='miniup_user'),
        'PASSWORD': env('DB_PASSWORD', default='miniup_secure_password_2025'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'prefer',
        }
    }
}
```

### 5. **Data Migration**
1. Exported all data from SQLite: `python manage.py dumpdata > data_backup_20251215_103923.json`
2. Ran migrations on PostgreSQL: `python manage.py migrate`
3. Imported data using custom script (with signals disabled): `python load_data_no_signals.py data_backup_20251215_103923.json`

### 6. **Verification**
- ✅ System check: No issues
- ✅ Data migrated: 2 users, 3 products, 2 wallets
- ✅ Server running successfully on PostgreSQL

---

## 🚀 Benefits of PostgreSQL

1. **Production Ready**: PostgreSQL is enterprise-grade and production-ready
2. **Better Performance**: Faster queries, better indexing, query optimization
3. **Concurrent Connections**: Handles multiple concurrent users efficiently
4. **Data Integrity**: Better ACID compliance and data consistency
5. **Advanced Features**: 
   - Full-text search
   - JSON/JSONB support
   - Geographic data (PostGIS)
   - Complex queries and aggregations
6. **Scalability**: Easy to scale horizontally with replication
7. **Backup & Recovery**: Better tools for backup and point-in-time recovery

---

## 🔐 Security Notes for Production

### Change Default Password
```bash
sudo -u postgres psql -d miniup_db
ALTER USER miniup_user WITH PASSWORD 'your_super_secure_random_password';
```

### Update Environment Variables
Create `.env` file:
```bash
DB_NAME=miniup_db
DB_USER=miniup_user
DB_PASSWORD=your_super_secure_random_password
DB_HOST=localhost
DB_PORT=5432
```

### Configure pg_hba.conf for Remote Access (if needed)
Edit `/etc/postgresql/14/main/pg_hba.conf`:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    miniup_db       miniup_user     0.0.0.0/0              scram-sha-256
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## 📋 Common PostgreSQL Commands

### Access PostgreSQL as postgres user
```bash
sudo -u postgres psql
```

### Connect to specific database
```bash
sudo -u postgres psql -d miniup_db
```

### List all databases
```sql
\l
```

### List all tables
```sql
\dt
```

### Show table structure
```sql
\d table_name
```

### Backup database
```bash
sudo -u postgres pg_dump miniup_db > backup_$(date +%Y%m%d).sql
```

### Restore database
```bash
sudo -u postgres psql miniup_db < backup_20251215.sql
```

### Check database size
```sql
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database
WHERE datname = 'miniup_db';
```

### Vacuum and analyze (optimize)
```sql
VACUUM ANALYZE;
```

---

## 🔄 Django Management with PostgreSQL

### Create backup with Django
```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission \
  --exclude admin.logentry --exclude sessions.session \
  --indent 2 > backup.json
```

### Restore backup
```bash
python manage.py loaddata backup.json
```

### Reset database (DANGER!)
```bash
python manage.py flush --no-input
python manage.py migrate
```

### Create superuser
```bash
python manage.py createsuperuser
```

---

## 🌐 Production Deployment Checklist

- [ ] Change database password to strong random value
- [ ] Update `.env` file with production credentials
- [ ] Configure `pg_hba.conf` for proper access control
- [ ] Enable SSL/TLS for PostgreSQL connections
- [ ] Set up automated backups (daily/weekly)
- [ ] Configure connection pooling (pgBouncer)
- [ ] Monitor database performance
- [ ] Set up replication for high availability
- [ ] Configure firewall rules
- [ ] Enable PostgreSQL logging

---

## 📈 Performance Tuning (Optional)

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB

# Connections
max_connections = 100

# Logging
log_statement = 'mod'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d '
```

Then restart:
```bash
sudo systemctl restart postgresql
```

---

## 📞 Support

For PostgreSQL issues:
- Official Docs: https://www.postgresql.org/docs/
- Django PostgreSQL: https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes

---

**Last Updated**: December 15, 2025  
**PostgreSQL Version**: 14.20  
**Django Version**: 4.2.26
