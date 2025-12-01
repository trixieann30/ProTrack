import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts.models import CustomUser
from decouple import config

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_email_settings():
    """Test email configuration"""
    print_section("EMAIL CONFIGURATION")
    
    print(f"📧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"📧 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 IS_PRODUCTION: {settings.IS_PRODUCTION}")
    
    # Check SendGrid configuration
    sendgrid_key = config('SENDGRID_API_KEY', default='')
    if sendgrid_key:
        print(f"✅ SendGrid API Key: {sendgrid_key[:10]}...")
        print(f"✅ Key starts with 'SG.': {sendgrid_key.startswith('SG.')}")
    else:
        print("❌ SendGrid API Key: NOT FOUND")
    
    print()
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️ Using Console Backend - Emails will print to terminal")
        print("   This is OK for development")
        return 'console'
    elif settings.EMAIL_BACKEND == 'sendgrid_backend.SendgridBackend':
        print("✅ Using SendGrid Backend - Emails will be sent via SendGrid")
        return 'sendgrid'
    else:
        print(f"❓ Unknown backend: {settings.EMAIL_BACKEND}")
        return 'unknown'

def test_notification_preferences(user):
    """Check user's notification preferences"""
    print_section("NOTIFICATION PREFERENCES")
    
    from accounts.models import NotificationPreference
    prefs, created = NotificationPreference.objects.get_or_create(user=user)
    
    print(f"👤 User: {user.username}")
    print()
    print("📧 EMAIL NOTIFICATIONS:")
    print(f"   Enrollment:  {'✅ ON' if prefs.email_on_enrollment else '❌ OFF'}")
    print(f"   Completion:  {'✅ ON' if prefs.email_on_completion else '❌ OFF'}")
    print(f"   Certificate: {'✅ ON' if prefs.email_on_certificate else '❌ OFF'}")
    print(f"   Assignment:  {'✅ ON' if prefs.email_on_assignment else '❌ OFF'}")
    print(f"   Reminder:    {'✅ ON' if prefs.email_on_reminder else '❌ OFF'}")
    
    print()
    print("🔔 IN-APP NOTIFICATIONS:")
    print(f"   Enrollment:   {'✅ ON' if prefs.notify_on_enrollment else '❌ OFF'}")
    print(f"   Completion:   {'✅ ON' if prefs.notify_on_completion else '❌ OFF'}")
    print(f"   Certificate:  {'✅ ON' if prefs.notify_on_certificate else '❌ OFF'}")
    print(f"   Assignment:   {'✅ ON' if prefs.notify_on_assignment else '❌ OFF'}")
    print(f"   Reminder:     {'✅ ON' if prefs.notify_on_reminder else '❌ OFF'}")
    print(f"   Announcement: {'✅ ON' if prefs.notify_on_announcement else '❌ OFF'}")
    
    return prefs

def test_send_test_email(user):
    """Send a test email to verify configuration"""
    print_section("SENDING TEST EMAIL")
    
    print(f"📤 Recipient: {user.email} ({user.username})")
    print("📨 Sending test email...")
    print()
    
    try:
        result = send_mail(
            subject='ProTrack - Test Email',
            message='This is a test email from ProTrack.\n\nIf you receive this, email notifications are working correctly!\n\nBest regards,\nThe ProTrack Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        print(f"✅ Email sent successfully! (Result: {result})")
        print()
        
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            print("📋 Check your terminal/console for the email content")
        else:
            print("📬 Check your inbox:", user.email)
            print("   💡 Don't forget to check your spam folder!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        print()
        print("🔍 Debug Information:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        return False

def test_enrollment_notification(user):
    """Test enrollment notification email"""
    print_section("TESTING ENROLLMENT EMAIL")
    
    from dashboard.models import TrainingCourse, Enrollment, Notification
    
    # Get an active course
    course = TrainingCourse.objects.filter(status='active').first()
    if not course:
        print("❌ No active courses found. Create a course first.")
        return False
    
    print(f"📚 Course: {course.title}")
    
    # Check if already enrolled
    existing = Enrollment.objects.filter(user=user, course=course).first()
    if existing:
        print(f"⚠️ Already enrolled (Status: {existing.status})")
        enrollment = existing
    else:
        print("📝 Creating test enrollment...")
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status='enrolled'
        )
        print(f"✅ Enrollment created (ID: {enrollment.id})")
    
    print()
    print("🔔 Creating enrollment notification...")
    
    try:
        notification = Notification.create_enrollment_notification(enrollment)
        
        if notification:
            print(f"✅ Notification created (ID: {notification.id})")
        else:
            print("⚠️ No notification created (toggle might be OFF)")
        
        print()
        print("📬 Check your email and notification bell!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("\n")
    print("🔔" * 35)
    print(" " * 20 + "EMAIL NOTIFICATION TEST SUITE")
    print("🔔" * 35)
    
    # Step 1: Test email configuration
    backend_type = test_email_settings()
    
    # Step 2: Get test user
    print_section("SELECT TEST USER")
    users = CustomUser.objects.filter(is_active=True).order_by('id')
    print("Available users:")
    for i, user in enumerate(users[:10], 1):
        print(f"  {i}. {user.username} ({user.email})")
    
    print()
    user_input = input("Enter user number (or username): ").strip()
    
    try:
        if user_input.isdigit():
            user = users[int(user_input) - 1]
        else:
            user = CustomUser.objects.get(username=user_input)
    except (IndexError, CustomUser.DoesNotExist):
        print("❌ User not found!")
        return
    
    print(f"✅ Selected: {user.username} ({user.email})")
    
    # Step 3: Check notification preferences
    prefs = test_notification_preferences(user)
    
    # Step 4: Send test email
    email_success = test_send_test_email(user)
    
    if not email_success:
        print()
        print("⚠️ Email test failed. Check your email configuration.")
        return
    
    # Step 5: Test enrollment notification
    print()
    proceed = input("\n🔔 Test enrollment notification? (y/n): ").strip().lower()
    if proceed == 'y':
        test_enrollment_notification(user)
    
    # Summary
    print_section("TEST SUMMARY")
    print()
    print("✅ Configuration test complete!")
    print()
    print("📋 Next Steps:")
    print("   1. Check your email inbox for test email")
    print("   2. Check notification bell in ProTrack")
    print("   3. Test other notification types")
    print()
    print("💡 If emails aren't working:")
    print("   - Verify SendGrid API key is correct")
    print("   - Check spam folder")
    print("   - Verify FROM email is authorized in SendGrid")
    print("   - Check SendGrid dashboard for delivery logs")
    print()

if __name__ == '__main__':
    main()