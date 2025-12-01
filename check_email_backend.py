#!/usr/bin/env python
"""
Quick Email Backend Check
Run: python check_email_backend.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from django.conf import settings
from decouple import config

print("\n" + "=" * 70)
print("  📧 EMAIL BACKEND CHECK")
print("=" * 70)

print(f"\n🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"🔧 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"🔧 IS_PRODUCTION: {settings.IS_PRODUCTION}")

sendgrid_key = config('SENDGRID_API_KEY', default='')

print("\n" + "-" * 70)

if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    print("\n✅ CONSOLE BACKEND (Development Mode)")
    print("   📺 Emails will PRINT TO TERMINAL ONLY")
    print("   ❌ NO real emails will be sent")
    print("   ✅ Safe for testing - won't spam anyone")
    print("\n   When you run test_email_config.py:")
    print("   → Email content appears in your terminal")
    print("   → Nothing sent to real email address")
    
elif settings.EMAIL_BACKEND == 'sendgrid_backend.SendgridBackend':
    print("\n✅ SENDGRID BACKEND (Production Mode)")
    print("   📧 REAL EMAILS will be sent via SendGrid")
    print("   ✅ Emails will arrive in actual inbox")
    print(f"   🔑 API Key: {sendgrid_key[:15]}..." if sendgrid_key else "   ❌ API Key: NOT FOUND")
    
    print("\n   When you run test_email_config.py:")
    print("   → Real email sent to the user's email address")
    print("   → Check your inbox (and spam folder)")
    print("   → May take 1-2 minutes to arrive")
    
    if not sendgrid_key or not sendgrid_key.startswith('SG.'):
        print("\n   ⚠️  WARNING: SendGrid API key may be invalid!")
        print("   → Key should start with 'SG.'")
        print("   → Check your .env file")
else:
    print(f"\n❓ UNKNOWN BACKEND: {settings.EMAIL_BACKEND}")

print("\n" + "=" * 70)

# Ask user if they want to continue
print("\n🤔 Do you want to send a test email now?")
print("   If using Console Backend: Email prints to terminal")
print("   If using SendGrid: REAL email sent to inbox")

choice = input("\nContinue? (y/n): ").strip().lower()

if choice == 'y':
    print("\n✅ Run: python test_email_config.py")
else:
    print("\n❌ Cancelled. No emails sent.")

print()