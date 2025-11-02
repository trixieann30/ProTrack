# Role-Based Permissions & File Upload Guide

## ✅ What's Fixed

### 1. Reports Menu Link
- **Before:** Placeholder link (`href="#"`)
- **After:** Working link to `/dashboard/reports/`
- **Access:** Admin only (automatically hidden for students/employees)

---

## 👥 User Roles & Permissions

### Role Overview

| Role | Access Level | Can Do |
|------|--------------|--------|
| **Administrator** | Full Access | Everything |
| **Employee** | Standard User | View, enroll, complete courses |
| **Student** | Standard User | View, enroll, complete courses |

---

## 🔐 Current Permission Structure

### What Each Role Can See

#### 🛡️ **Administrator** (Superuser)
**Menu Items:**
- ✅ Home
- ✅ Profile
- ✅ Training Catalog
- ✅ My Training
- ✅ **Assign Training** (Admin only)
- ✅ Certifications
- ✅ Settings
- ✅ **Reports** (Admin only)

**Special Abilities:**
- Assign training to users
- View all enrollments
- View all certificates
- Access analytics dashboard
- Manage users in Django Admin
- Upload training materials
- Issue certificates

---

#### 👔 **Employee** / 🎓 **Student**
**Menu Items:**
- ✅ Home
- ✅ Profile
- ✅ Training Catalog
- ✅ My Training
- ✅ Certifications
- ✅ Settings

**Abilities:**
- Browse training catalog
- Enroll in courses
- Track their own progress
- View their own certificates
- Update their profile
- Download course materials

**Cannot See:**
- Assign Training (hidden)
- Reports (hidden)
- Other users' data

---

## 📁 File Upload Functionality

### Current Status

**Backend:** ✅ Ready (Supabase integration complete)
**Frontend:** ⚠️ Needs upload forms

---

### Implementation Plan

### Option 1: Admin Uploads Materials (Recommended)

**Who:** Admin only
**Where:** Django Admin or custom admin interface
**What:** Upload PDFs, videos, presentations for courses

#### A. Using Django Admin (Already Works!)

1. Go to `/admin/dashboard/trainingmaterial/`
2. Click "Add Training Material"
3. Fill in:
   - Course
   - Title
   - Material Type
   - File URL (after uploading to Supabase)
   - File Name
   - File Size

#### B. Create Custom Upload Form

Add to `dashboard/forms.py`:

```python
from django import forms
from .models import TrainingMaterial

class TrainingMaterialUploadForm(forms.ModelForm):
    file = forms.FileField(
        label='Upload File',
        help_text='Max file size: 50MB'
    )
    
    class Meta:
        model = TrainingMaterial
        fields = ['course', 'title', 'description', 'material_type', 'is_required', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].widget.attrs.update({'class': 'form-select'})
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['material_type'].widget.attrs.update({'class': 'form-select'})
```

Add view to `dashboard/views.py`:

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import TrainingMaterialUploadForm
from .supabase_utils import upload_training_material

@login_required
@user_passes_test(is_superuser)
def upload_material(request, course_id):
    """Admin uploads training material"""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    if request.method == 'POST':
        form = TrainingMaterialUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Upload to Supabase
            file = request.FILES['file']
            success, url, error = upload_training_material(course_id, file)
            
            if success:
                # Save to database
                material = form.save(commit=False)
                material.file_url = url
                material.file_name = file.name
                material.file_size = file.size
                material.uploaded_by = request.user
                material.save()
                
                messages.success(request, 'Material uploaded successfully!')
                return redirect('dashboard:course_detail', course_id=course_id)
            else:
                messages.error(request, f'Upload failed: {error}')
    else:
        form = TrainingMaterialUploadForm(initial={'course': course})
    
    return render(request, 'dashboard/upload_material.html', {
        'form': form,
        'course': course
    })
```

Add URL:

```python
# In dashboard/urls.py
path('course/<int:course_id>/upload-material/', views.upload_material, name='upload_material'),
```

Create template `templates/dashboard/upload_material.html`:

```html
{% extends 'dashboard/base_dashboard.html' %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h5>Upload Training Material for {{ course.title }}</h5>
    </div>
    <div class="card-body">
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            
            <div class="mb-3">
                <label class="form-label">Course</label>
                <input type="text" class="form-control" value="{{ course.title }}" disabled>
                {{ form.course.as_hidden }}
            </div>
            
            <div class="mb-3">
                <label class="form-label">Title *</label>
                {{ form.title }}
            </div>
            
            <div class="mb-3">
                <label class="form-label">Description</label>
                {{ form.description }}
            </div>
            
            <div class="mb-3">
                <label class="form-label">Material Type *</label>
                {{ form.material_type }}
            </div>
            
            <div class="mb-3">
                <label class="form-label">Upload File *</label>
                {{ form.file }}
                <small class="text-muted">Supported: PDF, DOCX, PPTX, MP4, etc.</small>
            </div>
            
            <div class="mb-3 form-check">
                {{ form.is_required }}
                <label class="form-check-label">
                    Required for course completion
                </label>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Display Order</label>
                {{ form.order }}
            </div>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-upload me-2"></i>Upload Material
            </button>
            <a href="{% url 'dashboard:course_detail' course.id %}" class="btn btn-secondary">
                Cancel
            </a>
        </form>
    </div>
</div>
{% endblock %}
```

---

### Option 2: Students/Employees Upload Assignments (Optional)

**Who:** All users
**Where:** Course detail page
**What:** Upload assignment submissions

This would require:
1. New `Assignment` model
2. New `AssignmentSubmission` model
3. Upload form for students
4. Grading interface for admins

---

## 🎯 Quick Implementation Steps

### Step 1: Test Reports Link (Already Fixed!)

1. Login as **admin**
2. Check sidebar - Reports should be visible
3. Click Reports - should go to `/dashboard/reports/`
4. Logout and login as **student/employee**
5. Reports should be hidden

### Step 2: Verify Role-Based Access

**Test as Admin:**
```
✅ Can see "Assign Training"
✅ Can see "Reports"
✅ Can access /dashboard/reports/
✅ Can access /dashboard/training/assign/
```

**Test as Student/Employee:**
```
✅ Cannot see "Assign Training"
✅ Cannot see "Reports"
❌ Gets 403 error if tries to access /dashboard/reports/
❌ Gets 403 error if tries to access /dashboard/training/assign/
```

### Step 3: Add Upload Button to Course Detail (Admin Only)

Update `templates/dashboard/course_detail.html`:

```html
<!-- Add after course header, before materials section -->
{% if user.is_superuser %}
<div class="card mb-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0">Admin Actions</h6>
                <small class="text-muted">Manage course materials and settings</small>
            </div>
            <div>
                <a href="{% url 'dashboard:upload_material' course.id %}" 
                   class="btn btn-primary">
                    <i class="fas fa-upload me-2"></i>Upload Material
                </a>
            </div>
        </div>
    </div>
</div>
{% endif %}
```

---

## 📊 Permission Matrix

### Page Access Control

| Page | Admin | Employee | Student |
|------|-------|----------|---------|
| Training Catalog | ✅ | ✅ | ✅ |
| My Training | ✅ | ✅ | ✅ |
| Course Detail | ✅ | ✅ | ✅ |
| Certifications | ✅ | ✅ | ✅ |
| Settings | ✅ | ✅ | ✅ |
| **Assign Training** | ✅ | ❌ | ❌ |
| **Reports** | ✅ | ❌ | ❌ |
| **Upload Materials** | ✅ | ❌ | ❌ |
| **Django Admin** | ✅ | ❌ | ❌ |

### Action Permissions

| Action | Admin | Employee | Student |
|--------|-------|----------|---------|
| View courses | ✅ | ✅ | ✅ |
| Enroll in courses | ✅ | ✅ | ✅ |
| Track progress | ✅ | ✅ | ✅ |
| Download materials | ✅ | ✅ | ✅ |
| View own certificates | ✅ | ✅ | ✅ |
| **Assign training** | ✅ | ❌ | ❌ |
| **Upload materials** | ✅ | ❌ | ❌ |
| **Issue certificates** | ✅ | ❌ | ❌ |
| **View all users** | ✅ | ❌ | ❌ |
| **View analytics** | ✅ | ❌ | ❌ |

---

## 🔒 Security Implementation

### View-Level Protection

All admin-only views use `@user_passes_test(is_superuser)`:

```python
@login_required
@user_passes_test(is_superuser)
def reports(request):
    # Only admins can access
    ...

@login_required
@user_passes_test(is_superuser)
def assign_training(request):
    # Only admins can access
    ...
```

### Template-Level Protection

Menu items hidden based on role:

```html
{% if user.is_superuser %}
    <!-- Admin-only menu items -->
{% endif %}
```

### URL-Level Protection

Even if someone tries to access URL directly, they get 403 error.

---

## 📝 Summary

### ✅ What's Working Now

1. **Reports Link Fixed**
   - Admin: Can see and access Reports
   - Student/Employee: Reports hidden from menu

2. **Role-Based Menu**
   - Admin sees: All menu items
   - Student/Employee sees: Limited menu items

3. **Permission Enforcement**
   - Views protected with decorators
   - Templates hide unauthorized content
   - URLs return 403 for unauthorized access

### 🔧 What You Can Add (Optional)

1. **File Upload Form**
   - Admin uploads materials via custom form
   - Integrates with Supabase storage
   - See code snippets above

2. **Assignment Submissions**
   - Students upload assignment files
   - Admins grade submissions
   - Requires new models

3. **Bulk Actions**
   - Admin assigns training to multiple users
   - Admin uploads multiple files
   - Batch certificate generation

---

## 🚀 Next Steps

1. **Test the Reports link** - Login as admin and click Reports
2. **Verify role access** - Login as student/employee and confirm Reports is hidden
3. **Optional:** Add upload form using code above
4. **Optional:** Create assignment submission feature

Your system now has proper role-based access control! 🎉
