#!/usr/bin/env python
"""
Digest Email Test Script
Run: python test_digest_emails.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser, NotificationPreference
from dashboard.models import Notification


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_test_notifications(user, count=5):
    """Create test notifications for digest"""
    print_section("CREATING TEST NOTIFICATIONS")
    
    notification_types = [
        ('enrollment', 'Test Enrollment', 'You have been enrolled in a test course'),
        ('completion', 'Test Completion', 'You completed a test course'),
        ('certificate', 'Test Certificate', 'Your certificate is ready'),
        ('reminder', 'Test Reminder', 'This is a test reminder'),
        ('announcement', 'Test Announcement', 'This is a test announcement'),
    ]
    
    created = []
    for i in range(count):
        notif_type, title, message = notification_types[i % len(notification_types)]
        
        notification = Notification.objects.create(
            user=user,
            notification_type=notif_type,
            title=f'{title} #{i+1}',
            message=f'{message} (Test notification)',
            is_read=False
        )
        created.append(notification)
        print(f"✅ Created: {notification.title} (ID: {notification.id})")
    
    print(f"\n✅ Created {len(created)} test notifications")
    return created


def send_daily_digest_manual(user):
    """Manually send daily digest"""
    print_section("SENDING DAILY DIGEST")
    
    prefs = NotificationPreference.objects.get(user=user)
    
    if not prefs.daily_digest:
        print("❌ Daily digest is OFF for this user")
        print("   Enable it in: /dashboard/settings/notifications/")
        return False
    
    # Get unread notifications from last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    notifications = Notification.objects.filter(
        user=user,
        created_at__gte=yesterday,
        is_read=False
    ).order_by('-created_at')
    
    if not notifications.exists():
        print("⚠️  No unread notifications from last 24 hours")
        print("   Creating test notifications...")
        create_test_notifications(user, count=3)
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:3]
    
    print(f"📧 Found {notifications.count()} unread notifications")
    
    # Build email content
    subject = f'ProTrack Daily Digest - {notifications.count()} notifications'
    
    message_lines = [
        f'Hello {user.get_full_name() or user.username},',
        '',
        f'You have {notifications.count()} unread notifications:',
        '',
    ]
    
    for notif in notifications:
        message_lines.append(f'• {notif.title}')
        message_lines.append(f'  {notif.message}')
        if notif.link:
            message_lines.append(f'  Link: {settings.SITE_URL}{notif.link}')
        message_lines.append('')
    
    message_lines.extend([
        '',
        f'View all notifications: {settings.SITE_URL}/dashboard/notifications/',
        '',
        'Best regards,',
        'The ProTrack Team'
    ])
    
    message = '\n'.join(message_lines)
    
    print()
    print("📤 Sending daily digest email...")
    print(f"   To: {user.email}")
    print(f"   Subject: {subject}")
    
    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        print(f"✅ Daily digest sent successfully! (Result: {result})")
        
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            print("\n📋 Email content printed above in console")
        else:
            print(f"\n📬 Check inbox: {user.email}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to send digest: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_weekly_digest_manual(user):
    """Manually send weekly digest"""
    print_section("SENDING WEEKLY DIGEST")
    
    prefs = NotificationPreference.objects.get(user=user)
    
    if not prefs.weekly_digest:
        print("❌ Weekly digest is OFF for this user")
        print("   Enable it in: /dashboard/settings/notifications/")
        return False
    
    # Get notifications from last 7 days
    last_week = timezone.now() - timedelta(days=7)
    notifications = Notification.objects.filter(
        user=user,
        created_at__gte=last_week
    ).order_by('-created_at')
    
    if not notifications.exists():
        print("⚠️  No notifications from last 7 days")
        print("   Creating test notifications...")
        create_test_notifications(user, count=5)
        notifications = Notification.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
    
    unread_count = notifications.filter(is_read=False).count()
    
    print(f"📧 Found {notifications.count()} notifications ({unread_count} unread)")
    
    # Build email content
    subject = f'ProTrack Weekly Digest - {notifications.count()} notifications'
    
    message_lines = [
        f'Hello {user.get_full_name() or user.username},',
        '',
        f'Your weekly summary ({unread_count} unread):',
        '',
    ]
    
    # Group by notification type
    by_type = {}
    for notif in notifications:
        notif_type = notif.get_notification_type_display()
        if notif_type not in by_type:
            by_type[notif_type] = []
        by_type[notif_type].append(notif)
    
    for notif_type, notifs in by_type.items():
        message_lines.append(f'{notif_type.upper()} ({len(notifs)}):')
        
        for notif in notifs[:5]:  # Show max 5 per type
            status = '🔵' if not notif.is_read else '✅'
            message_lines.append(f'  {status} {notif.title}')
        
        if len(notifs) > 5:
            message_lines.append(f'  ... and {len(notifs) - 5} more')
        
        message_lines.append('')
    
    message_lines.extend([
        '',
        f'View all notifications: {settings.SITE_URL}/dashboard/notifications/',
        '',
        'Best regards,',
        'The ProTrack Team'
    ])
    
    message = '\n'.join(message_lines)
    
    print()
    print("📤 Sending weekly digest email...")
    print(f"   To: {user.email}")
    print(f"   Subject: {subject}")
    
    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        print(f"✅ Weekly digest sent successfully! (Result: {result})")
        
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            print("\n📋 Email content printed above in console")
        else:
            print(f"\n📬 Check inbox: {user.email}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to send digest: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("\n")
    print("📊" * 35)
    print(" " * 20 + "DIGEST EMAIL TEST SUITE")
    print("📊" * 35)
    
    # Select user
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
    
    # Check preferences
    print_section("NOTIFICATION PREFERENCES")
    prefs, created = NotificationPreference.objects.get_or_create(user=user)
    
    print(f"Daily Digest: {'✅ ON' if prefs.daily_digest else '❌ OFF'}")
    print(f"Weekly Digest: {'✅ ON' if prefs.weekly_digest else '❌ OFF'}")
    
    if not prefs.daily_digest and not prefs.weekly_digest:
        print()
        print("⚠️  Both digests are OFF!")
        enable = input("Enable them now? (y/n): ").strip().lower()
        
        if enable == 'y':
            prefs.daily_digest = True
            prefs.weekly_digest = True
            prefs.save()
            print("✅ Digests enabled!")
    
    # Menu
    while True:
        print_section("TEST MENU")
        print("1. Create test notifications")
        print("2. Send daily digest")
        print("3. Send weekly digest")
        print("4. View current notifications")
        print("5. Exit")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            count = input("How many notifications? (default 5): ").strip()
            count = int(count) if count.isdigit() else 5
            create_test_notifications(user, count)
        
        elif choice == '2':
            send_daily_digest_manual(user)
        
        elif choice == '3':
            send_weekly_digest_manual(user)
        
        elif choice == '4':
            print_section("CURRENT NOTIFICATIONS")
            notifs = Notification.objects.filter(user=user).order_by('-created_at')[:10]
            print(f"Total notifications: {Notification.objects.filter(user=user).count()}")
            print(f"Unread: {Notification.objects.filter(user=user, is_read=False).count()}")
            print()
            for notif in notifs:
                status = '🔵' if not notif.is_read else '✅'
                print(f"{status} {notif.title} - {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        elif choice == '5':
            break
    
    print()
    print("✅ Test complete!")
    print()


if __name__ == '__main__':
    main()