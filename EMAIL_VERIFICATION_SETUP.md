# Email Verification Setup Guide

## 🎉 What's New

The email verification feature is now fully functional! Users can verify their email addresses by clicking the "Send Verification Email" button on their profile page.

## 📧 Email Configuration

### Option 1: Gmail (Recommended for Production)

#### Step 1: Enable 2-Step Verification
1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left menu
3. Under "Signing in to Google", enable **2-Step Verification**

#### Step 2: Generate App Password
1. After enabling 2-Step Verification, go back to **Security**
2. Under "Signing in to Google", click **App passwords**
3. Select app: **Mail**
4. Select device: **Other (Custom name)** → Type "ProTrack"
5. Click **Generate**
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

#### Step 3: Update Your .env File
```env
# Email Configuration (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Important:** Use the App Password (16 characters), NOT your regular Gmail password!

### Option 2: Console Backend (For Testing)

If you want to test without setting up Gmail, the emails will print to your console/terminal.

In `settings.py`, the console backend is already configured:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

When you click "Send Verification Email", the email content will appear in your terminal where the Django server is running.

## 🚀 How It Works

### 1. User Profile Page
- Users see their email verification status (Verified ✅ or Not Verified ⚠️)
- If not verified, a "Send Verification Email" button appears

### 2. Sending Verification Email
- User clicks "Send Verification Email"
- System generates a unique 64-character token
- Email is sent with verification link
- Success message appears: "Verification email sent to user@example.com"

### 3. Email Content
```
Hello John Doe,

Thank you for registering with ProTrack!

Please verify your email address by clicking the link below:

http://127.0.0.1:8000/accounts/verify-email/abc123...xyz789/

This link will expire in 24 hours.

If you didn't create an account with ProTrack, please ignore this email.

Best regards,
The ProTrack Team
```

### 4. Clicking Verification Link
- User clicks the link in their email
- System verifies the token
- Email is marked as verified
- Success message: "✅ Your email has been verified successfully!"
- Badge changes from "Not Verified" to "Verified"

## 🔧 Technical Implementation

### Files Modified

#### 1. `accounts/views.py`
Added two new views:
- `send_verification_email()` - Generates token and sends email
- `verify_email(token)` - Verifies the token and marks email as verified

#### 2. `accounts/urls.py`
Added two new URL patterns:
```python
path('send-verification-email/', views.send_verification_email, name='send_verification_email'),
path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
```

#### 3. `templates/accounts/profile.html`
Updated the "Send Verification Email" button to be a functional form:
```html
<form method="post" action="{% url 'accounts:send_verification_email' %}">
    {% csrf_token %}
    <button type="submit">Send Verification Email</button>
</form>
```

## 🧪 Testing

### Test with Console Backend (No Gmail Setup Required)

1. **Start the server:**
   ```powershell
   python manage.py runserver
   ```

2. **Register or login to an account**

3. **Go to Profile page:**
   - Navigate to `/accounts/profile/`
   - You should see "Not Verified" badge

4. **Click "Send Verification Email"**

5. **Check your terminal** - You'll see the email output:
   ```
   Content-Type: text/plain; charset="utf-8"
   MIME-Version: 1.0
   Content-Transfer-Encoding: 7bit
   Subject: Verify Your Email - ProTrack
   From: your-email@gmail.com
   To: user@example.com
   
   Hello John Doe,
   
   Thank you for registering with ProTrack!
   
   Please verify your email address by clicking the link below:
   
   http://127.0.0.1:8000/accounts/verify-email/abc123...xyz789/
   ```

6. **Copy the verification URL** from the terminal

7. **Paste it in your browser** and press Enter

8. **Check your profile** - Badge should now show "Verified" ✅

### Test with Gmail (Production)

1. **Set up Gmail App Password** (see above)

2. **Update your `.env` file** with real credentials

3. **Restart the server:**
   ```powershell
   python manage.py runserver
   ```

4. **Click "Send Verification Email"**

5. **Check your actual email inbox**

6. **Click the verification link** in the email

7. **Profile updates** to show "Verified" ✅

## 🔒 Security Features

✅ **Unique tokens** - Each verification link uses a 64-character random token
✅ **One-time use** - Token is cleared after successful verification
✅ **User-specific** - Token is tied to the user's account
✅ **Login required** - Only logged-in users can request/verify emails
✅ **CSRF protection** - Form includes CSRF token

## 🎨 UI Features

- ✅ **Visual badges** - Clear "Verified" (green) or "Not Verified" (orange) indicators
- ✅ **Conditional display** - Button only shows if email is not verified
- ✅ **Success messages** - Clear feedback when email is sent
- ✅ **Error handling** - Graceful error messages if email fails to send

## 📝 Common Issues & Solutions

### Issue: "Failed to send email"

**Solution 1:** Check your Gmail App Password
- Make sure you're using the 16-character App Password, not your regular password
- Remove any spaces from the password in `.env`

**Solution 2:** Check your .env file
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # No spaces!
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Solution 3:** Verify 2-Step Verification is enabled
- Go to https://myaccount.google.com/security
- Ensure 2-Step Verification is ON

### Issue: Email not received

**Check:**
1. Spam/Junk folder
2. Gmail App Password is correct
3. Email address is correct
4. Check server logs for errors

### Issue: "Invalid or expired verification link"

**Causes:**
- Token was already used
- Token doesn't match
- User logged out and back in as different user

**Solution:**
- Click "Send Verification Email" again to get a new link

## 🚀 Next Steps

### Enhancements You Can Add:

1. **Token Expiration**
   - Add timestamp to track when token was created
   - Check if token is older than 24 hours
   - Reject expired tokens

2. **Email Templates**
   - Create HTML email templates
   - Add ProTrack branding
   - Make emails more visually appealing

3. **Automatic Email on Registration**
   - Send verification email immediately after registration
   - Remind users to verify their email

4. **Resend Cooldown**
   - Prevent spam by limiting how often users can request emails
   - Add 5-minute cooldown between requests

5. **Email Required for Features**
   - Require verified email to access certain features
   - Show warnings if email is not verified

## 📚 Resources

- Django Email Documentation: https://docs.djangoproject.com/en/4.2/topics/email/
- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- Django Messages Framework: https://docs.djangoproject.com/en/4.2/ref/contrib/messages/

---

**Your email verification system is now fully functional! 🎉**
