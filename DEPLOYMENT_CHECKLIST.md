# ProTrack Deployment Checklist for Render.com

## 🔴 Critical: Fix Google OAuth Error

Your app is showing "Internal Server Error" because Google OAuth is not configured for production. Follow these steps:

### 1. Update Google Cloud Console (5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your ProTrack project
3. Go to **APIs & Services** > **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Add these to **Authorized JavaScript origins**:
   ```
   https://protrackskillmanagement.onrender.com
   ```
6. Add these to **Authorized redirect URIs**:
   ```
   https://protrackskillmanagement.onrender.com/accounts/google/login/callback/
   ```
   ⚠️ **IMPORTANT**: Include the trailing slash `/`
7. Click **Save**

### 2. Update Site Domain in Production Database

**Method A: Using Management Command (Easiest)**

SSH into your Render service or use the Render Shell, then run:

```bash
python manage.py update_site_domain
```

This will automatically set the domain to `protrackskillmanagement.onrender.com`.

**Method B: Using Django Shell**

```bash
python manage.py shell
```

Then paste:

```python
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = 'protrackskillmanagement.onrender.com'
site.name = 'ProTrack Production'
site.save()
print(f"Site updated: {site.domain}")
exit()
```

**Method C: Via Django Admin**

1. Go to `https://protrackskillmanagement.onrender.com/admin/`
2. Login with superuser
3. Click **Sites** > **Sites**
4. Edit the site:
   - Domain: `protrackskillmanagement.onrender.com`
   - Name: `ProTrack Production`
5. Save

### 3. Verify Environment Variables on Render

Go to your Render dashboard > ProTrack service > Environment tab.

Ensure these are set:

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
SECRET_KEY=your-django-secret-key
DEBUG=False
DB_HOST=your-supabase-host
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_PORT=5432
```

### 4. Deploy Updated Code

Commit and push your changes:

```bash
git add .
git commit -m "Fix: Add production domain for Google OAuth"
git push origin main
```

Render will automatically redeploy.

### 5. Verify Social Application

After deployment:

1. Go to `https://protrackskillmanagement.onrender.com/admin/`
2. Navigate to **Social Applications**
3. Click on your Google OAuth app
4. Verify:
   - Provider: Google
   - Client ID: Matches your Google Console
   - Secret: Matches your Google Console
   - Sites: `protrackskillmanagement.onrender.com` is in "Chosen sites"
5. If not, add it and save

### 6. Test Google Login

1. Clear browser cache/cookies
2. Go to `https://protrackskillmanagement.onrender.com/accounts/login/`
3. Click "Sign in with Google"
4. Should work now! ✅

---

## Full Production Deployment Checklist

### Pre-Deployment

- [x] Code is working locally
- [ ] All migrations created and tested
- [ ] Static files collected
- [ ] Environment variables documented
- [ ] Database backup created (if applicable)

### Render Configuration

- [ ] Service created on Render
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn protrack.wsgi:application`
- [ ] Environment variables set (see above)
- [ ] Auto-deploy enabled from main branch

### Django Settings

- [x] `DEBUG = False` in production
- [x] `ALLOWED_HOSTS` includes production domain
- [x] `CSRF_TRUSTED_ORIGINS` includes production domain
- [x] `SECRET_KEY` is from environment variable
- [ ] Database configured (Supabase PostgreSQL)
- [ ] Static files configured
- [ ] Media files configured (if needed)

### Database

- [ ] Migrations applied: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`
- [ ] Site domain updated (see Step 2 above)
- [ ] Social application configured

### Google OAuth

- [x] Production domain added to Google Console
- [x] Redirect URI added to Google Console
- [ ] Site domain updated in Django
- [ ] Social application verified
- [ ] Environment variables set on Render

### Security

- [ ] `DEBUG = False`
- [ ] Strong `SECRET_KEY` set
- [ ] HTTPS enforced
- [ ] CSRF protection enabled
- [ ] Secure cookies configured
- [ ] SQL injection protection (Django ORM)
- [ ] XSS protection enabled

### Testing

- [ ] Homepage loads
- [ ] Admin panel accessible
- [ ] User registration works
- [ ] User login works (username/email)
- [ ] Google OAuth login works
- [ ] Dashboard accessible
- [ ] Training catalog works
- [ ] User management works (admin)
- [ ] All static files load correctly

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Test all critical features
- [ ] Verify email sending (if configured)
- [ ] Check database connections
- [ ] Monitor performance
- [ ] Set up error tracking (Sentry, etc.)

---

## Quick Commands for Render Shell

```bash
# Check current site
python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get_current())"

# Update site domain
python manage.py update_site_domain

# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Check for issues
python manage.py check --deploy
```

---

## Troubleshooting

### Error: "Internal Server Error"
- Check Render logs
- Verify environment variables
- Ensure migrations are applied
- Check database connection

### Error: "redirect_uri_mismatch"
- Verify Google Console redirect URI exactly matches
- Include `https://` and trailing `/`
- Clear browser cache

### Error: "Invalid client"
- Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Render
- Verify they match Google Console

### Error: "CSRF verification failed"
- Add domain to `CSRF_TRUSTED_ORIGINS` in settings.py
- Redeploy

### Google login button not showing
- Check Social Application is configured
- Verify site domain is correct
- Check template includes Google login

---

## Support

If you encounter issues:

1. Check Render logs: Dashboard > Your Service > Logs
2. Check Django logs
3. Verify all environment variables
4. Test locally with production settings
5. Review this checklist again

## Next Steps After OAuth Fix

1. Test all features thoroughly
2. Set up monitoring and alerts
3. Configure email for password resets
4. Set up regular database backups
5. Add custom domain (optional)
6. Configure CDN for static files (optional)
