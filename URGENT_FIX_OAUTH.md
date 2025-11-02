# 🚨 URGENT: Fix Google OAuth Error on Production

## The Problem
Your site `https://protrackskillmanagement.onrender.com` shows "Internal Server Error" because Google OAuth is not configured for your production domain.

## The Solution (3 Steps - 10 minutes)

### ✅ Step 1: Update Google Cloud Console (5 min)

1. **Go to**: [Google Cloud Console](https://console.cloud.google.com/)

2. **Select** your ProTrack project (top dropdown)

3. **Navigate to**: APIs & Services → Credentials

4. **Click** on your OAuth 2.0 Client ID (the one you created for ProTrack)

5. **Under "Authorized JavaScript origins"**, click **"+ ADD URI"** and add:
   ```
   https://protrackskillmanagement.onrender.com
   ```

6. **Under "Authorized redirect URIs"**, click **"+ ADD URI"** and add:
   ```
   https://protrackskillmanagement.onrender.com/accounts/google/login/callback/
   ```
   ⚠️ **CRITICAL**: Must include the trailing slash `/`

7. **Click SAVE** at the bottom

### ✅ Step 2: Update Django Site Domain (3 min)

**Option A: Run the Fix Script (Easiest)**

On your Render server shell, run:
```bash
python fix_production_oauth.py
```

**Option B: Use Management Command**
```bash
python manage.py update_site_domain
```

**Option C: Django Admin (If you can access it)**
1. Go to: `https://protrackskillmanagement.onrender.com/admin/`
2. Login with superuser
3. Click: **Sites** → **Sites** → Click on the site
4. Change **Domain name** to: `protrackskillmanagement.onrender.com`
5. Change **Display name** to: `ProTrack Production`
6. Click **Save**

**Option D: Django Shell (Manual)**
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
print(f"✅ Updated to: {site.domain}")
exit()
```

### ✅ Step 3: Verify & Deploy (2 min)

1. **Commit and push** your updated code:
   ```bash
   git add .
   git commit -m "Fix: Add production OAuth configuration"
   git push origin main
   ```

2. **Wait for Render** to automatically redeploy (watch the dashboard)

3. **Test**: Go to `https://protrackskillmanagement.onrender.com/accounts/login/`

4. **Click** "Sign in with Google" - should work now! ✅

---

## Verification Checklist

After completing the steps above, verify:

- [ ] Google Console has `https://protrackskillmanagement.onrender.com` in Authorized origins
- [ ] Google Console has `https://protrackskillmanagement.onrender.com/accounts/google/login/callback/` in Redirect URIs
- [ ] Django Site domain is set to `protrackskillmanagement.onrender.com`
- [ ] Code is pushed and Render has redeployed
- [ ] Can access the login page without errors
- [ ] Google login button appears
- [ ] Clicking Google login redirects to Google (not error)

---

## Still Not Working?

### Check Environment Variables on Render

1. Go to Render Dashboard → Your Service → Environment
2. Verify these exist:
   - `GOOGLE_CLIENT_ID` = your-client-id.apps.googleusercontent.com
   - `GOOGLE_CLIENT_SECRET` = GOCSPX-your-secret
   - `SECRET_KEY` = (your Django secret)
   - `DEBUG` = False

### Check Social Application in Django Admin

1. Go to: `https://protrackskillmanagement.onrender.com/admin/socialaccount/socialapp/`
2. You should see a Google OAuth app
3. Click on it and verify:
   - **Provider**: Google
   - **Client ID**: Matches Google Console
   - **Secret**: Matches Google Console  
   - **Sites**: `protrackskillmanagement.onrender.com` is in "Chosen sites"

If no Social Application exists, create one:
1. Click "Add Social Application"
2. Provider: Google
3. Name: Google OAuth
4. Client ID: (from Google Console)
5. Secret key: (from Google Console)
6. Sites: Select `protrackskillmanagement.onrender.com` and move to "Chosen sites"
7. Save

### Check Render Logs

```bash
# In Render dashboard, go to Logs tab
# Look for errors related to:
# - Site matching query does not exist
# - SocialApp matching query does not exist
# - redirect_uri_mismatch
```

---

## Quick Reference

**Your Production URL**: `https://protrackskillmanagement.onrender.com`

**Google Redirect URI**: `https://protrackskillmanagement.onrender.com/accounts/google/login/callback/`

**Django Admin**: `https://protrackskillmanagement.onrender.com/admin/`

**Login Page**: `https://protrackskillmanagement.onrender.com/accounts/login/`

---

## Need More Help?

See detailed guides:
- `PRODUCTION_OAUTH_FIX.md` - Detailed OAuth fix guide
- `DEPLOYMENT_CHECKLIST.md` - Full deployment checklist
- `GOOGLE_OAUTH_SETUP.md` - Complete OAuth setup guide

## Summary

The error happens because:
1. ❌ Google doesn't recognize your production domain
2. ❌ Django thinks the site is still `example.com` or `localhost`

The fix:
1. ✅ Tell Google about your production domain
2. ✅ Tell Django about your production domain
3. ✅ Redeploy

**Time needed**: ~10 minutes
**Difficulty**: Easy (just follow the steps!)
