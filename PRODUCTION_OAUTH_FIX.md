# Fix Google OAuth for Production (Render.com)

## Problem
Google OAuth is blocking authorization because your production domain `https://protrackskillmanagement.onrender.com` is not authorized in Google Cloud Console.

## Solution

### Step 1: Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your ProTrack project
3. Navigate to **APIs & Services** > **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized JavaScript origins**, ADD:
   ```
   https://protrackskillmanagement.onrender.com
   ```

6. Under **Authorized redirect URIs**, ADD:
   ```
   https://protrackskillmanagement.onrender.com/accounts/google/login/callback/
   ```
   ⚠️ **Important**: Include the trailing slash!

7. Click **Save**

### Step 2: Update Django Site Configuration

You need to update the Site domain in your production database:

**Option A: Via Django Admin (Recommended)**
1. Go to `https://protrackskillmanagement.onrender.com/admin/`
2. Log in with your superuser account
3. Navigate to **Sites** > **Sites**
4. Click on the existing site
5. Change:
   - **Domain name**: `protrackskillmanagement.onrender.com`
   - **Display name**: `ProTrack Production`
6. Click **Save**

**Option B: Via Django Shell**
```python
# SSH into your Render server or use Render shell
python manage.py shell

from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = 'protrackskillmanagement.onrender.com'
site.name = 'ProTrack Production'
site.save()
exit()
```

### Step 3: Verify Social Application

1. In Django Admin, go to **Social Applications**
2. Click on your Google OAuth app
3. Make sure the **Sites** includes `protrackskillmanagement.onrender.com`
4. If not, add it to "Chosen sites"
5. Click **Save**

### Step 4: Update Settings for Production

Make sure your `settings.py` has the correct configuration:

```python
# In settings.py
ALLOWED_HOSTS = [
    'protrackskillmanagement.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Make sure CSRF trusted origins includes your domain
CSRF_TRUSTED_ORIGINS = [
    'https://protrackskillmanagement.onrender.com',
]
```

### Step 5: Set Environment Variables on Render

1. Go to your Render dashboard
2. Select your ProTrack service
3. Go to **Environment** tab
4. Make sure these variables are set:
   - `GOOGLE_CLIENT_ID`: Your Google Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google Client Secret
   - `SECRET_KEY`: Your Django secret key
   - `DEBUG`: False (for production)

### Step 6: Test

1. Clear your browser cache/cookies
2. Go to `https://protrackskillmanagement.onrender.com/accounts/login/`
3. Click "Sign in with Google"
4. You should now be able to authenticate!

## Quick Fix Commands

If you have access to Render shell:

```bash
# Update site domain
python manage.py shell -c "from django.contrib.sites.models import Site; site = Site.objects.get_current(); site.domain = 'protrackskillmanagement.onrender.com'; site.name = 'ProTrack'; site.save(); print('Site updated!')"

# Verify
python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get_current())"
```

## Common Issues

### Issue: "redirect_uri_mismatch"
- **Cause**: Redirect URI doesn't match Google Console
- **Fix**: Ensure exact match including `https://` and trailing `/`

### Issue: "Invalid client"
- **Cause**: Wrong Client ID/Secret in environment variables
- **Fix**: Double-check Render environment variables

### Issue: Still showing localhost
- **Cause**: Site not updated in database
- **Fix**: Follow Step 2 above

### Issue: CSRF verification failed
- **Cause**: Missing CSRF_TRUSTED_ORIGINS
- **Fix**: Add to settings.py (see Step 4)

## Verification Checklist

- [ ] Google Cloud Console has production domain in Authorized origins
- [ ] Google Cloud Console has production callback URL in Redirect URIs
- [ ] Django Site domain is set to production URL
- [ ] Social Application is linked to correct site
- [ ] Environment variables are set on Render
- [ ] ALLOWED_HOSTS includes production domain
- [ ] CSRF_TRUSTED_ORIGINS includes production domain
