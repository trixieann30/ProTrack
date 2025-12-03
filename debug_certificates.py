import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'protrack.settings')
django.setup()

from dashboard.models import Certificate, Enrollment
from accounts.models import CustomUser
from decouple import config

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_supabase_config():
    """Check if Supabase is configured"""
    print_section("SUPABASE CONFIGURATION")
    
    supabase_url = config('SUPABASE_URL', default='')
    supabase_key = config('SUPABASE_KEY', default='')
    service_key = config('SUPABASE_SERVICE_KEY', default='')
    
    if supabase_url:
        print(f"✓ SUPABASE_URL: {supabase_url[:30]}...")
    else:
        print("✗ SUPABASE_URL: NOT FOUND")
    
    if supabase_key:
        print(f"✓ SUPABASE_KEY: {supabase_key[:20]}...")
    else:
        print("✗ SUPABASE_KEY: NOT FOUND")
    
    if service_key:
        print(f"✓ SUPABASE_SERVICE_KEY: {service_key[:20]}...")
    else:
        print("⚠ SUPABASE_SERVICE_KEY: NOT FOUND (using anon key)")
    
    return bool(supabase_url and supabase_key)

def check_certificates():
    """Check all certificates in database"""
    print_section("CERTIFICATE STATUS")
    
    certificates = Certificate.objects.all().select_related(
        'enrollment__user', 'enrollment__course'
    )
    
    print(f"\n📊 Total Certificates: {certificates.count()}")
    
    # Count by status
    draft = certificates.filter(status='draft').count()
    issued = certificates.filter(status='issued').count()
    revoked = certificates.filter(status='revoked').count()
    
    print(f"\n📋 Status Breakdown:")
    print(f"  • Draft (Pending): {draft}")
    print(f"  • Issued: {issued}")
    print(f"  • Revoked: {revoked}")
    
    # Show pending certificates
    if draft > 0:
        print(f"\n⏳ Pending Certificates:")
        for cert in certificates.filter(status='draft'):
            print(f"\n  Certificate #{cert.certificate_number}")
            print(f"    User: {cert.enrollment.user.username}")
            print(f"    Course: {cert.enrollment.course.title}")
            print(f"    Completion: {cert.enrollment.completion_date}")
            print(f"    Has URL: {'Yes' if cert.certificate_url else 'No'}")
    
    # Show issued certificates
    if issued > 0:
        print(f"\n✓ Issued Certificates:")
        for cert in certificates.filter(status='issued')[:5]:  # Show first 5
            print(f"\n  Certificate #{cert.certificate_number}")
            print(f"    User: {cert.enrollment.user.username}")
            print(f"    Issue Date: {cert.issue_date}")
            print(f"    Has URL: {'Yes ✓' if cert.certificate_url else 'No ✗'}")
            if cert.certificate_url:
                print(f"    URL: {cert.certificate_url[:50]}...")

def test_certificate_generation():
    """Test generating a certificate PDF"""
    print_section("TEST CERTIFICATE GENERATION")
    
    # Find a draft certificate
    cert = Certificate.objects.filter(status='draft').first()
    
    if not cert:
        print("⚠ No draft certificates found to test")
        return
    
    print(f"\n📝 Testing with certificate #{cert.certificate_number}")
    print(f"   User: {cert.enrollment.user.username}")
    print(f"   Course: {cert.enrollment.course.title}")
    
    try:
        from dashboard.views import generate_and_upload_certificate
        
        print("\n⏳ Generating and uploading certificate...")
        success, url = generate_and_upload_certificate(cert)
        
        if success:
            print(f"✓ Certificate generated successfully!")
            print(f"  URL: {url}")
            
            # Update certificate
            cert.status = 'issued'
            cert.certificate_url = url
            cert.save()
            print(f"✓ Certificate status updated to 'issued'")
        else:
            print(f"✗ Failed to generate certificate")
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        print("\n" + traceback.format_exc())

def main():
    print("\n")
    print("🔍" * 35)
    print(" " * 20 + "CERTIFICATE DEBUGGING")
    print("🔍" * 35)
    
    # Check Supabase
    supabase_ok = check_supabase_config()
    
    if not supabase_ok:
        print("\n⚠ WARNING: Supabase not configured properly!")
        print("  Certificate PDFs cannot be uploaded without Supabase")
        return
    
    # Check certificates
    check_certificates()
    
    # Ask if user wants to test generation
    print("\n" + "=" * 70)
    choice = input("\n🔧 Test certificate generation? (y/n): ").strip().lower()
    
    if choice == 'y':
        test_certificate_generation()
    
    print("\n" + "=" * 70)
    print("✓ Debugging complete!")
    print("\n📝 Next Steps:")
    print("  1. If certificates are stuck in 'draft', click 'Approve & Issue' in admin")
    print("  2. Check that Supabase bucket 'Uploadfiles' exists")
    print("  3. Verify admin user has permission to upload")
    print()

if __name__ == '__main__':
    main()