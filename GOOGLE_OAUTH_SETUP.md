# Google OAuth Setup Guide for ProTrack

## Prerequisites
- Google Account
- ProTrack Django application running

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter project name: `ProTrack` (or your preferred name)
5. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google+ API" or "People API"
3. Click on it and press **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: `ProTrack`
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue**
   - Scopes: Click **Save and Continue** (use defaults)
   - Test users: Add your email if needed
   - Click **Save and Continue**

4. Back to Create OAuth client ID:
   - Application type: **Web application**
   - Name: `ProTrack Web Client`
   
5. **Authorized JavaScript origins:**
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`

6. **Authorized redirect URIs:**
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://127.0.0.1:8000/accounts/google/login/callback/`

7. Click **Create**

8. **Copy your credentials:**
   - Client ID (looks like: `123456789-abc.apps.googleusercontent.com`)
   - Client Secret (looks like: `GOCSPX-abc123xyz`)

## Step 4: Configure ProTrack

1. Create a `.env` file in your ProTrack root directory (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Google credentials:
   ```
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

## Step 5: Add Google Provider in Django Admin

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to Django Admin: `http://127.0.0.1:8000/admin/`

3. Log in with your superuser account

4. Navigate to **Sites** > **Sites**
   - Click on `example.com`
   - Change Domain name to: `127.0.0.1:8000`
   - Change Display name to: `ProTrack`
   - Click **Save**

5. Navigate to **Social Applications** > **Add Social Application**
   - Provider: **Google**
   - Name: `Google OAuth`
   - Client id: Paste your Google Client ID
   - Secret key: Paste your Google Client Secret
   - Sites: Select `127.0.0.1:8000` and move it to "Chosen sites"
   - Click **Save**

## Step 6: Test Google Login

1. Go to `http://127.0.0.1:8000/accounts/login/`
2. Click "Sign in with Google"
3. Select your Google account
4. Grant permissions
5. You should be redirected back to ProTrack and logged in!

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Make sure the redirect URI in Google Cloud Console exactly matches:
  `http://127.0.0.1:8000/accounts/google/login/callback/`
- Note the trailing slash is important!

### Error: "Social application not found"
- Make sure you added the Social Application in Django Admin (Step 5)
- Check that the site domain matches exactly

### Error: "Invalid client"
- Double-check your Client ID and Secret in `.env`
- Make sure there are no extra spaces or quotes

### Google login button not showing
- Make sure `allauth.socialaccount.providers.google` is in INSTALLED_APPS
- Check that the template includes the Google login button

## Production Setup

For production, you'll need to:

1. Add your production domain to Google Cloud Console:
   - Authorized JavaScript origins: `https://yourdomain.com`
   - Authorized redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

2. Update the Site in Django Admin to your production domain

3. Verify your app in Google Cloud Console for public use

## Additional Resources

- [Django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
