#!/usr/bin/env python
"""
Quick fix script for Google OAuth on Render production
Run this on your Render server to fix the OAuth configuration
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


def main():
    print("🔧 ProTrack - Fixing Google OAuth for Production")
    print("=" * 50)
    print()
    
    # Step 1: Update site domain
    print("📍 Step 1: Updating site domain...")
    try:
        site = Site.objects.get_current()
        old_domain = site.domain
        
        site.domain = 'protrackskillmanagement.onrender.com'
        site.name = 'ProTrack Production'
        site.save()
        
        print(f"✅ Site domain updated from '{old_domain}' to '{site.domain}'")
    except Exception as e:
        print(f"❌ Error updating site: {e}")
        return False
    
    print()
    
    # Step 2: Verify configuration
    print("📋 Step 2: Verifying configuration...")
    print()
    
    print("Current Site:")
    site = Site.objects.get_current()
    print(f"  Domain: {site.domain}")
    print(f"  Name: {site.name}")
    print(f"  ID: {site.id}")
    print()
    
    print("Social Applications:")
    apps = SocialApp.objects.all()
    if apps.exists():
        for app in apps:
            print(f"  Provider: {app.provider}")
            print(f"  Name: {app.name}")
            print(f"  Client ID: {app.client_id[:20]}...")
            sites = [s.domain for s in app.sites.all()]
            print(f"  Sites: {sites}")
            
            # Check if production site is linked
            if 'protrackskillmanagement.onrender.com' not in sites:
                print("  ⚠️  WARNING: Production site not linked to this app!")
                print("     Go to Django Admin and add the site to this Social Application")
            else:
                print("  ✅ Production site is linked")
            print()
    else:
        print("  ⚠️  No social applications found!")
        print("     You need to create one in Django Admin:")
        print("     1. Go to /admin/socialaccount/socialapp/")
        print("     2. Add Social Application")
        print("     3. Provider: Google")
        print("     4. Add your Client ID and Secret")
        print("     5. Select the production site")
        print()
    
    print()
    print("✅ Configuration check complete!")
    print()
    print("📝 Next Steps:")
    print("=" * 50)
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. Navigate to: APIs & Services > Credentials")
    print()
    print("3. Click on your OAuth 2.0 Client ID")
    print()
    print("4. Add to 'Authorized JavaScript origins':")
    print("   https://protrackskillmanagement.onrender.com")
    print()
    print("5. Add to 'Authorized redirect URIs':")
    print("   https://protrackskillmanagement.onrender.com/accounts/google/login/callback/")
    print("   (Note: Include the trailing slash!)")
    print()
    print("6. Click 'Save' in Google Console")
    print()
    print("7. Test login at:")
    print("   https://protrackskillmanagement.onrender.com/accounts/login/")
    print()
    print("For detailed instructions, see PRODUCTION_OAUTH_FIX.md")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
