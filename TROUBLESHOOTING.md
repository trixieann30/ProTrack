# ProTrack Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "Page not found" or 404 Error

**Symptoms:**
- Clicking menu items shows "Page not found"
- URL shows 404 error

**Solutions:**

1. **Check if server is running:**
   ```bash
   python manage.py runserver
   ```

2. **Verify URL patterns:**
   - Training Catalog: `http://127.0.0.1:8000/dashboard/training/catalog/`
   - My Training: `http://127.0.0.1:8000/dashboard/training/my-training/`
   - Assign Training: `http://127.0.0.1:8000/dashboard/training/assign/`
   - Certifications: `http://127.0.0.1:8000/dashboard/certifications/`
   - Reports: `http://127.0.0.1:8000/dashboard/reports/`

3. **Check URL configuration:**
   ```bash
   python manage.py show_urls
   ```

---

### Issue 2: "Template does not exist"

**Symptoms:**
- Error: `TemplateDoesNotExist at /dashboard/reports/`
- Shows template name like `dashboard/reports.html`

**Solutions:**

1. **Create the template file:**
   ```
   dashboard/templates/dashboard/reports.html
   ```

2. **Check template directory structure:**
   ```
   ProTrack/
   ├── dashboard/
   │   ├── templates/
   │   │   └── dashboard/
   │   │       ├── training_catalog.html
   │   │       ├── my_training.html
   │   │       ├── certifications.html
   │   │       └── reports.html  ← Create this
   ```

3. **Temporary fix - create placeholder:**
   ```html
   {% extends 'base.html' %}
   
   {% block content %}
   <h1>Reports Dashboard</h1>
   <p>Reports page is under construction</p>
   {% endblock %}
   ```

---

### Issue 3: "Permission Denied" or 403 Error

**Symptoms:**
- Can't access Reports or Assign Training
- Shows "Permission denied" message

**Solutions:**

1. **Login as admin:**
   - Reports and Assign Training require superuser access
   - Create superuser if needed:
     ```bash
     python manage.py createsuperuser
     ```

2. **Check user permissions:**
   ```python
   python manage.py shell
   ```
   ```python
   from accounts.models import CustomUser
   user = CustomUser.objects.get(username='your-username')
   print(f"Is superuser: {user.is_superuser}")
   print(f"Is staff: {user.is_staff}")
   ```

3. **Make user superuser:**
   ```python
   user.is_superuser = True
   user.is_staff = True
   user.save()
   ```

---

### Issue 4: "No courses found" in Training Catalog

**Symptoms:**
- Training Catalog page loads but shows "No courses found"
- Empty course list

**Solutions:**

1. **Create test courses in Django Admin:**
   - Go to: `http://127.0.0.1:8000/admin/`
   - Navigate to: Dashboard → Training courses
   - Click "Add Training Course"

2. **Create via shell:**
   ```bash
   python manage.py shell
   ```
   ```python
   from dashboard.models import TrainingCategory, TrainingCourse
   
   # Create category
   cat = TrainingCategory.objects.create(
       name="Technical Skills",
       description="Technical training courses"
   )
   
   # Create course
   course = TrainingCourse.objects.create(
       title="Python Programming Basics",
       description="Learn Python from scratch",
       category=cat,
       instructor="John Doe",
       duration_hours=40,
       level="beginner",
       learning_outcomes="Understand Python syntax and basics",
       status="active"
   )
   
   print(f"Created: {course.title}")
   ```

---

### Issue 5: Database Connection Error

**Symptoms:**
- `OperationalError: connection refused`
- Can't connect to database

**Solutions:**

1. **Check `.env` file has correct credentials:**
   ```env
   DB_HOST=aws-1-us-east-2.pooler.supabase.com
   DB_PORT=6543
   DB_NAME=postgres
   DB_USER=postgres.zkpaqrzwoffzumhbeyfj
   DB_PASSWORD=dmsL62VTD1LL6QDY
   ```

2. **Test database connection:**
   ```bash
   python manage.py check --database default
   ```

3. **Check Supabase database is running:**
   - Go to: https://supabase.com/dashboard
   - Check project status

---

### Issue 6: Supabase Storage Not Working

**Symptoms:**
- File upload fails
- "Supabase credentials not configured" error

**Solutions:**

1. **Add SUPABASE_KEY to `.env`:**
   ```env
   SUPABASE_URL=https://zkpaqrzwoffzumhbeyfj.supabase.co
   SUPABASE_KEY=your-anon-public-key-here
   ```

2. **Get your Supabase key:**
   - Go to: https://supabase.com/dashboard/project/zkpaqrzwoffzumhbeyfj
   - Click: Settings → API
   - Copy: "anon/public" key

3. **Restart Django server** after adding key

4. **Test Supabase connection:**
   ```python
   python manage.py shell
   ```
   ```python
   from dashboard.supabase_utils import SupabaseStorage
   
   storage = SupabaseStorage()
   print(f"URL: {storage.supabase_url}")
   print(f"Key exists: {bool(storage.supabase_key)}")
   ```

---

### Issue 7: Migrations Not Applied

**Symptoms:**
- `no such table: dashboard_trainingmaterial`
- `no such table: dashboard_certificate`

**Solutions:**

1. **Check migration status:**
   ```bash
   python manage.py showmigrations dashboard
   ```

2. **Apply migrations:**
   ```bash
   python manage.py migrate dashboard
   ```

3. **If migrations are missing, create them:**
   ```bash
   python manage.py makemigrations dashboard
   python manage.py migrate dashboard
   ```

---

### Issue 8: Static Files Not Loading

**Symptoms:**
- CSS/JS not loading
- Page looks unstyled

**Solutions:**

1. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

2. **Check STATIC_URL in settings:**
   ```python
   STATIC_URL = '/static/'
   ```

3. **For development, ensure DEBUG=True:**
   ```env
   DEBUG=True
   ```

---

### Issue 9: Import Errors

**Symptoms:**
- `ImportError: cannot import name 'Certificate'`
- `ImportError: cannot import name 'TrainingMaterial'`

**Solutions:**

1. **Check models are defined:**
   ```bash
   python manage.py shell
   ```
   ```python
   from dashboard.models import Certificate, TrainingMaterial
   print("✅ Models imported successfully")
   ```

2. **If error persists, restart server:**
   - Stop server (Ctrl+C)
   - Start again: `python manage.py runserver`

---

### Issue 10: Reports Page Shows No Data

**Symptoms:**
- Reports page loads but all stats show 0
- No data in tables

**Solutions:**

1. **Create test data:**
   ```python
   python manage.py shell
   ```
   ```python
   from dashboard.models import *
   from accounts.models import CustomUser
   from django.utils import timezone
   
   # Create user
   user = CustomUser.objects.create_user(
       username='testuser',
       email='test@test.com',
       password='password123'
   )
   
   # Create category
   cat = TrainingCategory.objects.create(name="Test Category")
   
   # Create course
   course = TrainingCourse.objects.create(
       title="Test Course",
       description="Test",
       category=cat,
       instructor="Test Instructor",
       duration_hours=10,
       level="beginner",
       learning_outcomes="Test outcomes",
       status="active"
   )
   
   # Create enrollment
   Enrollment.objects.create(
       user=user,
       course=course,
       status="completed",
       progress_percentage=100,
       score=85.5,
       completion_date=timezone.now().date()
   )
   
   print("✅ Test data created!")
   ```

2. **Refresh the Reports page**

---

## Quick Diagnostic Commands

### Check Everything
```bash
# 1. Check system
python manage.py check

# 2. Check database
python manage.py check --database default

# 3. Check migrations
python manage.py showmigrations

# 4. Check if server runs
python manage.py runserver
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Access Django Admin
```
http://127.0.0.1:8000/admin/
```

### Test URLs
```
http://127.0.0.1:8000/dashboard/
http://127.0.0.1:8000/dashboard/training/catalog/
http://127.0.0.1:8000/dashboard/training/my-training/
http://127.0.0.1:8000/dashboard/training/assign/
http://127.0.0.1:8000/dashboard/certifications/
http://127.0.0.1:8000/dashboard/reports/
```

---

## Getting Help

### Check Logs
Look at the terminal where `runserver` is running for error messages.

### Django Shell
```bash
python manage.py shell
```

Test imports:
```python
from dashboard.models import *
from dashboard.views import *
from dashboard.supabase_utils import *
```

### Check Documentation
- `USER_STORIES_IMPLEMENTATION.md`
- `SUPABASE_SETUP_GUIDE.md`
- `NAVIGATION_MENU_IMPLEMENTATION.md`
- `REPORTS_IMPLEMENTATION.md`

---

## Common Error Messages and Fixes

| Error | Fix |
|-------|-----|
| `TemplateDoesNotExist` | Create the template file |
| `OperationalError` | Check database credentials |
| `ImportError` | Run migrations, restart server |
| `PermissionDenied` | Login as superuser |
| `404 Not Found` | Check URL pattern |
| `No such table` | Run migrations |
| `Supabase credentials not configured` | Add SUPABASE_KEY to .env |

---

## Still Not Working?

Please provide:
1. **Exact error message** (screenshot or text)
2. **Which page** you're trying to access
3. **What you see** vs what you expect
4. **Terminal output** from runserver

This will help diagnose the specific issue!
