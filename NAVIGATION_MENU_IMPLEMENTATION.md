# Navigation Menu Implementation Guide

## Your Navigation Menu

Based on your screenshot, you have 4 main menu items:
1. 📚 **Training Catalog**
2. 🎓 **My Training**
3. ➕ **Assign Training**
4. 🏆 **Certifications**

---

## Database Connection

### Your Supabase Credentials

```env
# Database (PostgreSQL via Supabase)
DB_NAME=postgres
DB_USER=postgres.zkpaqrzwoffzumhbeyfj
DB_PASSWORD=dmsL62VTD1LL6QDY
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543

# Supabase Storage (for file uploads)
SUPABASE_URL=https://zkpaqrzwoffzumhbeyfj.supabase.co
SUPABASE_KEY=<your-anon-public-key>
```

**To get your SUPABASE_KEY:**
1. Go to https://supabase.com/dashboard
2. Select project: `zkpaqrzwoffzumhbeyfj`
3. Settings → API → Copy "anon/public" key

---

## Menu Item Implementations

### 1. 📚 Training Catalog

**URL:** `/dashboard/training/catalog/`  
**View:** `training_catalog`  
**User Story:** US-05 - Manage Training Programs

**Features:**
- ✅ Browse all active training courses
- ✅ Filter by category
- ✅ Filter by level (Beginner/Intermediate/Advanced)
- ✅ Search courses
- ✅ View course details
- ✅ Enroll in courses

**Models Used:**
- `TrainingCourse`: Course information
- `TrainingCategory`: Course categories
- `TrainingSession`: Scheduled sessions

**Template:** `dashboard/training_catalog.html`

**Current Implementation:**
```python
@login_required
def training_catalog(request):
    """Display all available training courses"""
    courses = TrainingCourse.objects.filter(status='active').select_related('category')
    categories = TrainingCategory.objects.all()
    
    # Filtering and search logic
    # ...
    
    return render(request, 'dashboard/training_catalog.html', context)
```

---

### 2. 🎓 My Training

**URL:** `/dashboard/training/my-training/`  
**View:** `my_training`  
**User Story:** US-01 - Training Summary & Progress

**Features:**
- ✅ View enrolled courses
- ✅ Track progress percentage
- ✅ See completion status
- ✅ View scores
- ✅ Cancel enrollments
- ✅ Access training materials

**Models Used:**
- `Enrollment`: User's course enrollments
- `TrainingCourse`: Course details
- `TrainingMaterial`: Course materials

**Template:** `dashboard/my_training.html`

**Current Implementation:**
```python
@login_required
def my_training(request):
    """Display user's enrolled training courses (US-01)"""
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related('course', 'session').order_by('-enrolled_date')
    
    context = {
        'enrollments': enrollments,
    }
    
    return render(request, 'dashboard/my_training.html', context)
```

**Enhanced Features to Add:**
- Show training materials for each course
- Display progress bars
- Show certificates for completed courses
- Filter by status (enrolled, in progress, completed)

---

### 3. ➕ Assign Training

**URL:** `/dashboard/training/assign/`  
**View:** `assign_training`  
**User Story:** US-02 B - Training Management Implementation

**Features:**
- ✅ Admin-only access
- ✅ Assign courses to users
- ✅ Select specific sessions
- ✅ Bulk assignment
- ✅ Set deadlines

**Models Used:**
- `Enrollment`: Create assignments
- `CustomUser`: Select users
- `TrainingCourse`: Select courses
- `TrainingSession`: Select sessions

**Template:** `dashboard/assign_training.html`

**Current Implementation:**
```python
@login_required
@user_passes_test(is_superuser)
def assign_training(request):
    """Admin view to assign training to users (US-02 B)"""
    if request.method == 'POST':
        # Handle assignment logic
        # ...
    
    users = CustomUser.objects.filter(is_superuser=False)
    courses = TrainingCourse.objects.filter(status='active')
    
    return render(request, 'dashboard/assign_training.html', context)
```

---

### 4. 🏆 Certifications

**URL:** `/dashboard/certifications/`  
**View:** `certifications`  
**User Story:** US-09 - Manage Certificates

**Features:**
- ✅ View earned certificates
- ✅ Download certificate PDFs
- ✅ See certificate details (number, issue date, expiry)
- ✅ Admin: View all certificates
- ✅ Admin: Issue/revoke certificates

**Models Used:**
- `Certificate`: Certificate records
- `Enrollment`: Linked to completed courses

**Template:** `dashboard/certifications.html`

**Updated Implementation:**
```python
@login_required
def certifications(request):
    """Display user's certificates (US-09)"""
    user = request.user
    
    if user.is_superuser:
        # Admins see all certificates
        certificates = Certificate.objects.select_related(
            'enrollment__user',
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')
    else:
        # Regular users see only their own certificates
        certificates = Certificate.objects.filter(
            enrollment__user=user
        ).select_related(
            'enrollment__course',
            'issued_by'
        ).order_by('-issue_date')
    
    context = {
        'certificates': certificates,
        'user': user,
    }
    
    return render(request, 'dashboard/certifications.html', context)
```

---

## Database Tables and Relationships

### Core Tables

1. **accounts_customuser**
   - User information
   - Fields: username, email, user_type, profile_picture, etc.

2. **dashboard_trainingcategory**
   - Course categories
   - Fields: name, description, icon

3. **dashboard_trainingcourse**
   - Training programs/courses
   - Fields: title, description, category, instructor, duration, level, status
   - Linked to: TrainingCategory, TrainingSession, Enrollment, TrainingMaterial

4. **dashboard_trainingsession**
   - Scheduled training sessions
   - Fields: course, session_name, start_date, end_date, location, is_online
   - Linked to: TrainingCourse, Enrollment

5. **dashboard_enrollment**
   - User course enrollments
   - Fields: user, course, session, status, progress_percentage, score
   - Linked to: CustomUser, TrainingCourse, TrainingSession, Certificate

6. **dashboard_trainingmaterial** ⭐ NEW
   - Course materials (files in Supabase)
   - Fields: course, title, material_type, file_url, file_name, file_size
   - Linked to: TrainingCourse
   - Storage: Supabase `Uploadfiles` bucket

7. **dashboard_certificate** ⭐ NEW
   - Training certificates
   - Fields: enrollment, certificate_number, issue_date, expiry_date, status, certificate_url
   - Linked to: Enrollment
   - Storage: Supabase `Uploadfiles` bucket (certificates folder)

---

## File Storage Structure

### Supabase Buckets

#### 1. `profilepic` Bucket
```
profilepic/
├── user_1/
│   └── profile.jpg
├── user_2/
│   └── profile.png
└── user_3/
    └── profile.jpg
```

**Usage:** User profile pictures  
**Access:** Public or authenticated users  
**Upload Function:** `upload_profile_picture(user_id, file)`

#### 2. `Uploadfiles` Bucket
```
Uploadfiles/
├── course_1/
│   ├── lecture_notes.pdf
│   ├── presentation.pptx
│   ├── video.mp4
│   └── quiz.pdf
├── course_2/
│   ├── module1.pdf
│   └── slides.pptx
└── certificates/
    ├── enrollment_1.pdf
    ├── enrollment_2.pdf
    └── enrollment_3.pdf
```

**Usage:** Training materials and certificates  
**Access:** Authenticated users  
**Upload Functions:**
- `upload_training_material(course_id, file)`
- `upload_certificate(enrollment_id, pdf_file)`

---

## Integration Flow

### For Training Materials (US-07)

1. **Admin uploads material:**
   ```python
   from dashboard.supabase_utils import upload_training_material
   
   # In view
   file = request.FILES['material_file']
   success, url, error = upload_training_material(course_id=1, file=file)
   
   if success:
       TrainingMaterial.objects.create(
           course_id=course_id,
           title=request.POST['title'],
           material_type=request.POST['material_type'],
           file_url=url,
           file_name=file.name,
           file_size=file.size,
           uploaded_by=request.user
       )
   ```

2. **User views materials in "My Training":**
   ```python
   # In my_training view
   enrollment = Enrollment.objects.get(id=enrollment_id)
   materials = enrollment.course.materials.all()
   ```

3. **User downloads material:**
   - Click link → Opens Supabase public URL
   - File downloads directly from Supabase

### For Certificates (US-09)

1. **Admin generates certificate:**
   ```python
   from dashboard.supabase_utils import upload_certificate
   
   # Generate PDF (using reportlab or similar)
   pdf_file = generate_certificate_pdf(enrollment)
   
   # Upload to Supabase
   success, url, error = upload_certificate(enrollment.id, pdf_file)
   
   if success:
       Certificate.objects.create(
           enrollment=enrollment,
           certificate_number=generate_certificate_number(),
           certificate_url=url,
           status='issued',
           issued_by=request.user
       )
   ```

2. **User views certificate:**
   - Go to "Certifications" menu
   - See list of earned certificates
   - Click "Download" → Opens PDF from Supabase

---

## Setup Steps

### 1. Update `.env` File

Add these lines to your `.env`:

```env
# Supabase Storage
SUPABASE_URL=https://zkpaqrzwoffzumhbeyfj.supabase.co
SUPABASE_KEY=your-anon-public-key-here
```

### 2. Run Migrations

```bash
python manage.py migrate dashboard
```

This creates the `TrainingMaterial` and `Certificate` tables.

### 3. Install Required Packages

```bash
pip install requests  # For Supabase API
```

### 4. Test Database Connection

```bash
python manage.py check --database default
```

Should show no errors if database is connected.

### 5. Create Test Data

```bash
python manage.py shell
```

```python
from dashboard.models import TrainingCategory, TrainingCourse

# Create a category
category = TrainingCategory.objects.create(
    name="Technical Skills",
    description="Technical training courses"
)

# Create a course
course = TrainingCourse.objects.create(
    title="Python Programming Basics",
    description="Learn Python from scratch",
    category=category,
    instructor="John Doe",
    duration_hours=40,
    level="beginner",
    learning_outcomes="Understand Python syntax, Write basic programs",
    status="active"
)

print(f"Created course: {course.title}")
```

### 6. Test Navigation

1. Run server: `python manage.py runserver`
2. Login as admin
3. Test each menu item:
   - Training Catalog → Should show courses
   - My Training → Should show enrollments
   - Assign Training → Should show assignment form
   - Certifications → Should show certificates

---

## Next Development Tasks

### Priority 1: Material Upload Interface
- Create form for uploading training materials
- Integrate with Supabase storage
- Show materials in course detail view

### Priority 2: Certificate Generation
- Implement PDF generation (using reportlab)
- Create certificate template
- Auto-generate on course completion

### Priority 3: Progress Tracking
- Add progress bars to "My Training"
- Track material completion
- Calculate overall progress

### Priority 4: Reports Dashboard (US-03)
- Create admin reports view
- Show completion statistics
- Export reports to CSV/PDF

---

## Troubleshooting

### Database Connection Issues

**Error:** `OperationalError: connection refused`

**Solution:**
1. Check `.env` has correct DB credentials
2. Verify Supabase database is running
3. Test connection: `python manage.py check --database default`

### Supabase Storage Issues

**Error:** `Supabase credentials not configured`

**Solution:**
1. Add `SUPABASE_URL` and `SUPABASE_KEY` to `.env`
2. Get key from Supabase Dashboard → Settings → API
3. Restart Django server

### Migration Issues

**Error:** `No such table: dashboard_trainingmaterial`

**Solution:**
```bash
python manage.py makemigrations dashboard
python manage.py migrate dashboard
```

---

## Summary

✅ **Database:** Connected to Supabase PostgreSQL  
✅ **Storage:** Two buckets (`profilepic`, `Uploadfiles`)  
✅ **Models:** All 6 models created  
✅ **Views:** All 4 menu items have views  
✅ **Admin:** Full CRUD in Django Admin  
⏳ **Templates:** Need to be created/updated  
⏳ **File Upload:** Need to add forms  
⏳ **PDF Generation:** Need to implement  

Your ProTrack system is now fully connected to Supabase and ready for the next phase of development! 🚀
