# 🚨 URGENT: Fix MultipleObjectsReturned Error on Production

## Current Status
Production site is showing: `MultipleObjectsReturned at /accounts/google/login/`

## Root Cause
There are likely **multiple Google Social Applications** in the production database linked to the same site.

## Quick Fix (5 minutes)

### Option 1: Run the Fix Script (Recommended)

1. **SSH into Render** or open Render Shell
2. **Run this command:**
   ```bash
   python fix_production_multipleobjects.py
   ```
3. **Follow the output** - it will automatically fix the issue
4. **Restart the service** if needed

### Option 2: Manual Fix via Django Admin

1. Go to: `https://protrackskillmanagement.onrender.com/admin/`
2. Login with superuser credentials
3. Navigate to: **Social applications** → **Social applications**
4. Look for **multiple Google OAuth entries**
5. **Delete all but one** Google OAuth application
6. Make sure the remaining one is linked to the correct site

### Option 3: Django Shell

1. **Open Render Shell** or SSH
2. **Run:**
   ```bash
   python manage.py shell
   ```
3. **Paste this code:**
   ```python
   from allauth.socialaccount.models import SocialApp
   from django.contrib.sites.models import Site
   
   # Get current site
   site = Site.objects.get_current()
   print(f"Current site: {site.domain}")
   
   # Get all Google apps for this site
   apps = SocialApp.objects.filter(provider='google', sites=site)
   print(f"Google apps: {apps.count()}")
   
   # If more than 1, keep the first and delete others
   if apps.count() > 1:
       keep = apps.first()
       delete_apps = apps.exclude(id=keep.id)
       for app in delete_apps:
           print(f"Deleting: {app.name}")
           app.delete()
       print("Fixed!")
   else:
       print("Only one app found - issue might be elsewhere")
   
   exit()
   ```

## After Fixing

1. **Verify the fix:**
   - Go to `/admin/socialaccount/socialapp/`
   - Should see only **ONE** Google OAuth application
   - It should be linked to `protrackskillmanagement.onrender.com`

2. **Clear cache and test:**
   - Clear browser cache
   - Go to `/accounts/login/`
   - Click "Sign in with Google"
   - Should work now!

## If Still Not Working

### Check 1: Verify Latest Code is Deployed

The latest commit should be: `6a2c5b8 - Fix: Remove duplicate Google OAuth config`

**To verify:**
1. Go to Render Dashboard
2. Check "Events" tab
3. Latest deployment should show commit `6a2c5b8`
4. If not, manually trigger a redeploy

### Check 2: Verify Environment Variables

Make sure these are set in Render Environment:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `DEBUG=False`
- `SECRET_KEY` (production key)

See `ENV_VARS_FOR_RENDER.md` for complete list.

### Check 3: Check Render Logs

1. Go to Render Dashboard → Logs
2. Look for errors related to:
   - `MultipleObjectsReturned`
   - Database connection
   - OAuth configuration

## Files to Help

- `fix_production_multipleobjects.py` - Automated fix script
- `ENV_VARS_FOR_RENDER.md` - Required environment variables
- `ENVIRONMENT_VARIABLES.txt` - Simple text format

## Timeline

1. ✅ Code fix pushed (commit 6a2c5b8)
2. ⏳ Waiting for deployment
3. ⏳ Need to fix duplicate Social Apps in database
4. ⏳ Need to add environment variables

## Contact

If you need help or have questions, please reach out to the development team.

---

**Priority:** HIGH  
**Impact:** Production site Google login not working  
**Estimated fix time:** 5 minutes
