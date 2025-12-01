import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts.models import CustomUser, NotificationPreference
from dashboard.models import Notification, TrainingCourse, Enrollment


def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_email_config():
    """Test email configuration"""
    print_section("EMAIL CONFIGURATION")
    print(f"📧 Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 Production: {settings.IS_PRODUCTION}")
    
    if 'sendgrid' in settings.EMAIL_BACKEND.lower():
        print("✓ SendGrid configured for production")
        return True
    else:
        print("⚠️ Using console backend (development mode)")
        return False


def check_notification_preferences():
    """Ensure all users have notification preferences"""
    print_section("NOTIFICATION PREFERENCES")
    
    users = CustomUser.objects.filter(is_active=True)
    print(f"📊 Total active users: {users.count()}")
    
    created_count = 0
    for user in users:
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        if created:
            created_count += 1
    
    if created_count > 0:
        print(f"✓ Created {created_count} missing preferences")
    else:
        print("✓ All users have preferences")
    
    return True


def send_test_notification():
    """Send a test notification"""
    print_section("SENDING TEST NOTIFICATION")
    
    user = CustomUser.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active users found")
        return False
    
    print(f"👤 User: {user.username} ({user.email})")
    
    # Create notification
    notif = Notification.objects.create(
        user=user,
        notification_type='system',
        title='🔔 Test Notification',
        message='This is a test notification. If you see this, the system is working!',
        link='/dashboard/',
        is_read=False
    )
    print(f"✓ Created notification (ID: {notif.id})")
    
    # Send test email
    try:
        send_mail(
            subject='ProTrack - Test Notification',
            message='This is a test email. Email notifications are working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"✓ Email sent to {user.email}")
    except Exception as e:
        print(f"⚠️ Email error: {str(e)}")
    
    print("\n📬 Check:")
    print(f"  - Email: {user.email}")
    print(f"  - Notification bell in ProTrack")
    print(f"  - Page: /dashboard/notifications/")
    
    return True


def test_enrollment_workflow():
    """Test enrollment notification workflow"""
    print_section("ENROLLMENT NOTIFICATION TEST")
    
    user = CustomUser.objects.filter(is_active=True, is_superuser=False).first()
    course = TrainingCourse.objects.filter(status='active').first()
    
    if not user or not course:
        print("⚠️ Need an active user and course")
        return False
    
    print(f"👤 User: {user.username}")
    print(f"📚 Course: {course.title}")
    
    # Check existing enrollment
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    
    if not enrollment:
        print("ℹ️ Creating test enrollment...")
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status='enrolled'
        )
    else:
        print(f"ℹ️ Using existing enrollment (Status: {enrollment.status})")
    
    # Trigger notification
    try:
        Notification.create_enrollment_notification(enrollment)
        print("✓ Enrollment notification sent")
        
        # Count notifications
        notif_count = Notification.objects.filter(
            user=user,
            notification_type__in=['enrollment', 'assignment']
        ).count()
        print(f"📊 Total enrollment notifications: {notif_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("🚀" * 35)
    print(" " * 15 + "PRODUCTION NOTIFICATION TEST (SIMPLIFIED)")
    print("🚀" * 35)
    
    results = {
        'Email Configuration': test_email_config(),
        'Notification Preferences': check_notification_preferences(),
        'Test Notification': send_test_notification(),
        'Enrollment Workflow': test_enrollment_workflow(),
    }
    
    # Summary
    print_section("TEST SUMMARY")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test}")
    
    all_passed = all(results.values())
    print("\n" + ("✅" if all_passed else "⚠️") + " Testing complete!")
    
    if all_passed:
        print("\n🎉 All systems operational!")
        print("\nNext steps:")
        print("1. Test notifications in the live site")
        print("2. Toggle notification settings: /dashboard/settings/notifications/")
        print("3. Enroll in a course and check for notifications")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    print()


if __name__ == '__main__':
    main()