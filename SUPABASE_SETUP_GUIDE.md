# Supabase Storage Setup Guide for ProTrack

## Overview
This guide will help you set up Supabase Storage for ProTrack's file management features.

## Prerequisites
- Supabase account (https://supabase.com)
- ProTrack project
- Two storage buckets already created:
  - `profilepic` - For user profile pictures
  - `Uploadfiles` - For training materials and certificates

---

## Step 1: Get Supabase Credentials

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your ProTrack project
3. Navigate to **Settings** → **API**
4. Copy the following:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

---

## Step 2: Configure Environment Variables

Add these to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-key-here
```

**Example:**
```env
SUPABASE_URL=https://zkpaqrzwoffzumhbeyfj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprcGFxcnp3b2ZmenVtaGJleWZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODk1NjQwMDAsImV4cCI6MjAwNTE0MDAwMH0.xxxxx
```

---

## Step 3: Verify Bucket Configuration

### Check Bucket Settings

1. Go to **Storage** in Supabase Dashboard
2. Verify both buckets exist:
   - `profilepic`
   - `Uploadfiles`

### Make Buckets Public (Recommended for easier access)

For each bucket:
1. Click on the bucket name
2. Click **Settings** (gear icon)
3. Toggle **Public bucket** to ON
4. Click **Save**

**Note:** Public buckets allow files to be accessed via direct URLs without authentication.

### Set Bucket Policies (If keeping buckets private)

If you want to keep buckets private, you'll need to set up Row Level Security (RLS) policies.

**For `profilepic` bucket:**
```sql
-- Allow authenticated users to upload their own profile pictures
CREATE POLICY "Users can upload their own profile pictures"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'profilepic' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow public read access
CREATE POLICY "Public can view profile pictures"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'profilepic');
```

**For `Uploadfiles` bucket:**
```sql
-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'Uploadfiles');

-- Allow authenticated users to read files
CREATE POLICY "Authenticated users can view files"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'Uploadfiles');
```

---

## Step 4: Install Required Python Packages

```bash
pip install requests
```

This is required for making HTTP requests to Supabase Storage API.

---

## Step 5: Run Database Migrations

```bash
python manage.py migrate dashboard
```

This will create the `TrainingMaterial` and `Certificate` tables.

---

## Step 6: Test the Integration

### Test 1: Upload Profile Picture

```python
from dashboard.supabase_utils import upload_profile_picture
from django.core.files.uploadedfile import SimpleUploadedFile

# Create a test file
with open('test_image.jpg', 'rb') as f:
    file = SimpleUploadedFile('test.jpg', f.read(), content_type='image/jpeg')

# Upload
success, url, error = upload_profile_picture(user_id=1, file=file)

if success:
    print(f"Uploaded successfully: {url}")
else:
    print(f"Upload failed: {error}")
```

### Test 2: Upload Training Material

```python
from dashboard.supabase_utils import upload_training_material
from django.core.files.uploadedfile import SimpleUploadedFile

# Create a test file
with open('test_document.pdf', 'rb') as f:
    file = SimpleUploadedFile('document.pdf', f.read(), content_type='application/pdf')

# Upload
success, url, error = upload_training_material(course_id=1, file=file)

if success:
    print(f"Uploaded successfully: {url}")
else:
    print(f"Upload failed: {error}")
```

### Test 3: Check in Django Admin

1. Go to `/admin/`
2. Navigate to **Dashboard** → **Training materials**
3. Try creating a new material (you'll need to manually enter the file URL for now)
4. Verify the material appears in the list

---

## Step 7: File Upload Flow

### For Profile Pictures

1. User uploads file via form
2. Backend calls `upload_profile_picture(user_id, file)`
3. File is uploaded to `profilepic/user_{id}/profile.{ext}`
4. Public URL is returned
5. URL is saved to `CustomUser.profile_picture` field

### For Training Materials

1. Admin uploads file via form
2. Backend calls `upload_training_material(course_id, file)`
3. File is uploaded to `Uploadfiles/course_{id}/{filename}`
4. Public URL is returned
5. `TrainingMaterial` object is created with:
   - `file_url`: Public URL
   - `file_name`: Original filename
   - `file_size`: File size in bytes

### For Certificates

1. Admin generates certificate PDF
2. Backend calls `upload_certificate(enrollment_id, pdf_file)`
3. PDF is uploaded to `Uploadfiles/certificates/enrollment_{id}.pdf`
4. Public URL is returned
5. `Certificate` object is updated with `certificate_url`

---

## Troubleshooting

### Error: "Supabase credentials not configured"

**Solution:** Make sure `SUPABASE_URL` and `SUPABASE_KEY` are set in your `.env` file.

### Error: "Bucket not found"

**Solution:** 
1. Check bucket names are exactly `profilepic` and `Uploadfiles` (case-sensitive)
2. Verify buckets exist in Supabase Dashboard → Storage

### Error: "Upload failed: 403 Forbidden"

**Solution:**
1. Check if bucket is public OR
2. Set up proper RLS policies (see Step 3)
3. Verify your `SUPABASE_KEY` is correct

### Error: "Invalid file URL format"

**Solution:** Make sure file URLs follow this format:
```
https://your-project.supabase.co/storage/v1/object/public/bucketname/path/to/file.ext
```

### Files not accessible

**Solution:**
1. Make buckets public in Supabase Dashboard
2. OR set up proper RLS policies
3. Check file URLs are correct

---

## File Structure in Supabase

### profilepic bucket
```
profilepic/
├── user_1/
│   └── profile.jpg
├── user_2/
│   └── profile.png
└── user_3/
    └── profile.jpg
```

### Uploadfiles bucket
```
Uploadfiles/
├── course_1/
│   ├── lecture_notes.pdf
│   ├── presentation.pptx
│   └── video.mp4
├── course_2/
│   └── quiz.pdf
└── certificates/
    ├── enrollment_1.pdf
    ├── enrollment_2.pdf
    └── enrollment_3.pdf
```

---

## Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use anon/public key** - Not the service_role key (which has admin access)
3. **Set up RLS policies** - For production, implement proper access control
4. **Validate file types** - Check file extensions and MIME types before upload
5. **Limit file sizes** - Set maximum file size limits in your forms
6. **Scan for malware** - Consider integrating virus scanning for uploaded files

---

## Production Deployment

### For Render

Add environment variables in Render Dashboard:
1. Go to your ProTrack service
2. Click **Environment** tab
3. Add:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your anon/public key
4. Save and redeploy

### For Other Platforms

Make sure to set the environment variables in your hosting platform's configuration.

---

## Next Steps

1. ✅ Set up Supabase credentials
2. ✅ Run migrations
3. ✅ Test file uploads
4. ⏳ Implement file upload forms in views
5. ⏳ Add file validation
6. ⏳ Implement certificate PDF generation
7. ⏳ Add progress tracking views

---

## Support

- Supabase Documentation: https://supabase.com/docs/guides/storage
- ProTrack Issues: Check `USER_STORIES_IMPLEMENTATION.md`
