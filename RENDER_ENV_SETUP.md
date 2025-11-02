# Render Environment Variables Setup

## ✅ Your Correct Credentials

Based on your `.env` file, these are the **correct values** to set on Render:

### Database Configuration
```
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.zkpaqrzwoffzumhbeyfj
DB_PASSWORD=dmsL62VTD1LL6QDY
```

### Django Configuration
```
SECRET_KEY=<generate-a-new-secure-key-for-production>
DEBUG=False
```

### Email Configuration
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

## 🔧 How to Set Environment Variables on Render

### Step 1: Go to Render Dashboard
1. Open [Render Dashboard](https://dashboard.render.com/)
2. Click on your **ProTrack** service

### Step 2: Navigate to Environment Tab
1. Click on **Environment** in the left sidebar
2. You'll see a list of environment variables

### Step 3: Add/Update Each Variable
For each variable above:
1. Click **Add Environment Variable** (or edit existing)
2. Enter the **Key** (e.g., `DB_HOST`)
3. Enter the **Value** (e.g., `aws-1-us-east-2.pooler.supabase.com`)
4. Click **Save**

### Step 4: Save Changes
1. After adding all variables, click **Save Changes** at the bottom
2. Render will automatically **redeploy** your service
3. Wait 2-5 minutes for deployment to complete

## ⚠️ Important Notes

### SECRET_KEY for Production
Don't use the same SECRET_KEY as local development. Generate a new one:

**Option 1: Use Django's generator**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Option 2: Use online generator**
- Go to https://djecrety.ir/
- Copy the generated key

### DEBUG Setting
**CRITICAL:** Set `DEBUG=False` in production for security!

### Database Connection
Make sure you're using the **Connection Pooling** (pooler) endpoint from Supabase, not the direct connection. The pooler endpoint:
- Uses port `6543` (not `5432`)
- Has better performance for serverless deployments
- Format: `aws-1-us-east-2.pooler.supabase.com`

## 📋 Checklist

Before saving on Render, verify:

- [ ] `DB_HOST` = `aws-1-us-east-2.pooler.supabase.com` ✅
- [ ] `DB_PORT` = `6543` ✅
- [ ] `DB_NAME` = `postgres` ✅
- [ ] `DB_USER` = `postgres.zkpaqrzwoffzumhbeyfj` ✅
- [ ] `DB_PASSWORD` = `dmsL62VTD1LL6QDY` ✅
- [ ] `SECRET_KEY` = (new secure key for production) ⚠️
- [ ] `DEBUG` = `False` ⚠️
- [ ] `EMAIL_HOST_USER` = `protrack.appemail@gmail.com` ✅
- [ ] `EMAIL_HOST_PASSWORD` = `dwdtcrkwuadzltwb` ✅
- [ ] `DEFAULT_FROM_EMAIL` = `ProTrack` ✅
- [ ] `GOOGLE_CLIENT_ID` = `42322597281-2vv4kgataamcu3elqeb97ugm2hug6bib.apps.googleusercontent.com` ✅
- [ ] `GOOGLE_CLIENT_SECRET` = `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` ✅

## 🧪 Testing After Setup

Once Render finishes redeploying:

1. **Test database connection:**
   - Go to any page on your site
   - If no database errors, it's working! ✅

2. **Test Google OAuth:**
   - Go to `/accounts/login/`
   - Click "Sign in with Google"
   - Should redirect to Google and back successfully ✅

3. **Check logs:**
   - Go to Render Dashboard → Logs
   - Look for any errors
   - Should see successful startup messages

## 🚨 Troubleshooting

### Still getting database connection error?

1. **Double-check the password** - No extra spaces or quotes
2. **Verify Supabase is running** - Check Supabase dashboard
3. **Check Render logs** - Look for specific error messages
4. **Try direct connection** - Temporarily change to direct connection endpoint:
   - Host: `db.zkpaqrzwoffzumhbeyfj.supabase.co`
   - Port: `5432`

### OAuth still not working?

1. **Verify Google Cloud Console** has production domain
2. **Check Django Admin** - Social Application is configured
3. **Run fix script** on Render shell:
   ```bash
   python fix_production_oauth.py
   ```

## 📞 Quick Reference

**Your Supabase Project:** `zkpaqrzwoffzumhbeyfj`
**Pooler Host:** `aws-1-us-east-2.pooler.supabase.com`
**Pooler Port:** `6543`
**Production URL:** `https://protrackskillmanagement.onrender.com`

---

## Next Steps

1. ✅ Copy the environment variables above
2. ✅ Go to Render Dashboard → Environment
3. ✅ Add/update all variables
4. ✅ Generate new SECRET_KEY for production
5. ✅ Set DEBUG=False
6. ✅ Save changes
7. ⏳ Wait for Render to redeploy (2-5 minutes)
8. ✅ Test your site!

Good luck! 🚀
