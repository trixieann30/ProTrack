# Environment Variables for Render Deployment

**To:** Developer managing Render deployment  
**From:** ProTrack Development Team  
**Date:** November 2, 2025  
**Subject:** Required Environment Variables for ProTrack Production

---

## 🚨 URGENT: Missing Environment Variables Causing Production Errors

The production site is currently experiencing database connection errors because environment variables are not set on Render.

## Required Environment Variables

Please add/update these environment variables in the Render dashboard:

### Database Configuration (Supabase)
```
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.zkpaqrzwoffzumhbeyfj
DB_PASSWORD=dmsL62VTD1LL6QDY
```

### Django Configuration
```
SECRET_KEY=django-insecure-3ixyr7lvc=udrd!j_zsp_080h$419anora+thv!fa^8tie65so
DEBUG=False
```
⚠️ **Note:** Please generate a NEW SECRET_KEY for production using:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Email Configuration (Gmail)
```
EMAIL_HOST_USER=protrack.appemail@gmail.com
EMAIL_HOST_PASSWORD=dwdtcrkwuadzltwb
DEFAULT_FROM_EMAIL=ProTrack
```

### Google OAuth Configuration
```
GOOGLE_CLIENT_ID=42322597281-2vv4kgataamcu3elqeb97ugm2hug6bib.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
```

---

## How to Add These on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select the **ProTrack** service
3. Click **Environment** tab in the left sidebar
4. For each variable above:
   - Click **Add Environment Variable**
   - Enter the Key (e.g., `DB_HOST`)
   - Enter the Value (e.g., `aws-1-us-east-2.pooler.supabase.com`)
5. Click **Save Changes** at the bottom
6. Render will automatically redeploy (takes 2-5 minutes)

---

## Current Issues Being Fixed

### ✅ Issue 1: Google OAuth Error (FIXED in code)
- **Error:** `MultipleObjectsReturned at /accounts/google/login/`
- **Fix:** Removed duplicate OAuth configuration from settings.py
- **Status:** Fixed in latest commit (6a2c5b8)

### ❌ Issue 2: Database Connection Error (NEEDS ENV VARS)
- **Error:** `OperationalError: connection to server at "aws-1-us-east-2.pooler.supabase.com" failed`
- **Cause:** Missing database environment variables on Render
- **Fix:** Add the DB_* variables listed above

---

## Verification After Setup

Once you've added the environment variables and Render has redeployed:

1. **Check the site loads:** https://protrackskillmanagement.onrender.com/
2. **Test Google login:** https://protrackskillmanagement.onrender.com/accounts/login/
3. **Check Render logs** for any remaining errors

---

## Additional Information

### Latest Code Changes (Already Pushed to GitHub)
- Fixed admin user detail view variable names
- Removed duplicate Google OAuth configuration
- Added CSRF_TRUSTED_ORIGINS for production domain
- Added production domain to ALLOWED_HOSTS

### Files Modified in Latest Commit
- `protrack/settings.py` - OAuth and security fixes
- `dashboard/views.py` - Admin view fixes
- Added deployment documentation and utility scripts

### GitHub Repository
All changes have been pushed to the `main` branch and should auto-deploy once environment variables are set.

---

## Contact

If you have any questions about these environment variables or need clarification, please let me know.

**Important:** The site will not work properly until all these environment variables are added to Render.

---

## Quick Copy-Paste Format

If you prefer, here's a format you can copy-paste directly:

```
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.zkpaqrzwoffzumhbeyfj
DB_PASSWORD=dmsL62VTD1LL6QDY
SECRET_KEY=<generate-new-key>
DEBUG=False
EMAIL_HOST_USER=protrack.appemail@gmail.com
EMAIL_HOST_PASSWORD=dwdtcrkwuadzltwb
DEFAULT_FROM_EMAIL=ProTrack
GOOGLE_CLIENT_ID=42322597281-2vv4kgataamcu3elqeb97ugm2hug6bib.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
```

---

Thank you for your assistance in deploying these fixes! 🚀
