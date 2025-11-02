# Frontend Implementation Guide - Connecting User Stories

## Current Status

Your templates are **beautifully designed** but need to be **connected to the backend data** to fully implement the user stories.

---

## What's Already Working ✅

1. **Training Catalog** - Shows courses, filters work
2. **My Training** - Shows enrollments with progress bars
3. **Assign Training** - Admin can assign courses
4. **Certifications** - Page exists
5. **Reports** - View created (needs template)

---

## What Needs to Be Added 🔧

### 1. Training Materials (US-07)

**Current Issue:** Materials aren't shown in course details or My Training

**Solution:** Add materials section to templates

#### A. Update `course_detail.html`

Add this section to show training materials:

```html
<!-- Training Materials Section -->
<div class="card mt-4">
    <div class="card-header">
        <h5><i class="fas fa-folder-open me-2"></i>Training Materials</h5>
    </div>
    <div class="card-body">
        {% if course.materials.all %}
            <div class="list-group">
                {% for material in course.materials.all %}
                <a href="{{ material.file_url }}" target="_blank" 
                   class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-file-{{ material.material_type }} me-2"></i>
                            <strong>{{ material.title }}</strong>
                            {% if material.is_required %}
                                <span class="badge bg-danger ms-2">Required</span>
                            {% endif %}
                        </div>
                        <div class="text-muted">
                            <small>{{ material.file_size|filesizeformat }}</small>
                            <i class="fas fa-download ms-2"></i>
                        </div>
                    </div>
                    {% if material.description %}
                    <p class="mb-0 mt-2 text-muted">{{ material.description }}</p>
                    {% endif %}
                </a>
                {% endfor %}
            </div>
        {% else %}
            <p class="text-muted mb-0">
                <i class="fas fa-info-circle me-2"></i>
                No materials available yet
            </p>
        {% endif %}
    </div>
</div>
```

#### B. Update `my_training.html`

Add materials to each enrollment card:

```html
<!-- Add after progress section in training-card -->
{% if enrollment.course.materials.all %}
<div class="materials-section mt-3">
    <h6 class="text-muted mb-2">
        <i class="fas fa-folder me-2"></i>Course Materials
    </h6>
    <div class="d-flex flex-wrap gap-2">
        {% for material in enrollment.course.materials.all|slice:":3" %}
        <a href="{{ material.file_url }}" target="_blank" 
           class="btn btn-sm btn-outline-primary">
            <i class="fas fa-file-{{ material.material_type }} me-1"></i>
            {{ material.title }}
        </a>
        {% endfor %}
        {% if enrollment.course.materials.count > 3 %}
        <a href="{% url 'dashboard:course_detail' enrollment.course.id %}" 
           class="btn btn-sm btn-outline-secondary">
            +{{ enrollment.course.materials.count|add:"-3" }} more
        </a>
        {% endif %}
    </div>
</div>
{% endif %}
```

---

### 2. Certificates Display (US-09)

**Current Issue:** Certifications page doesn't show actual certificates

#### Update `certifications.html`

Replace the content with:

```html
{% extends 'dashboard/base_dashboard.html' %}
{% load static %}

{% block title %}Certifications - ProTrack{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h2 class="mb-1">
            <i class="fas fa-certificate me-2" style="color: #f59e0b;"></i>
            Certification Management
        </h2>
        <p class="text-muted mb-0">Track and manage your professional certifications</p>
    </div>
</div>

<!-- Statistics Cards -->
<div class="row g-4 mb-4">
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-muted mb-1">Active Certifications</h6>
                        <h3 class="mb-0">{{ certificates|length }}</h3>
                    </div>
                    <div class="text-success">
                        <i class="fas fa-certificate fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-muted mb-1">Expiring Soon</h6>
                        <h3 class="mb-0">0</h3>
                    </div>
                    <div class="text-warning">
                        <i class="fas fa-exclamation-triangle fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-muted mb-1">Expired</h6>
                        <h3 class="mb-0">0</h3>
                    </div>
                    <div class="text-danger">
                        <i class="fas fa-times-circle fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-muted mb-1">Total Certifications</h6>
                        <h3 class="mb-0">{{ certificates|length }}</h3>
                    </div>
                    <div class="text-primary">
                        <i class="fas fa-award fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- My Certifications -->
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">My Certifications</h5>
    </div>
    <div class="card-body">
        {% if certificates %}
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Certificate Number</th>
                            <th>Course</th>
                            <th>Issue Date</th>
                            <th>Expiry Date</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for cert in certificates %}
                        <tr>
                            <td>
                                <strong>{{ cert.certificate_number }}</strong>
                            </td>
                            <td>
                                {{ cert.enrollment.course.title }}
                            </td>
                            <td>
                                {{ cert.issue_date|date:"M d, Y" }}
                            </td>
                            <td>
                                {% if cert.expiry_date %}
                                    {{ cert.expiry_date|date:"M d, Y" }}
                                {% else %}
                                    <span class="text-muted">No expiry</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if cert.status == 'issued' %}
                                    <span class="badge bg-success">
                                        <i class="fas fa-check me-1"></i>Valid
                                    </span>
                                {% elif cert.status == 'revoked' %}
                                    <span class="badge bg-danger">
                                        <i class="fas fa-ban me-1"></i>Revoked
                                    </span>
                                {% else %}
                                    <span class="badge bg-secondary">
                                        {{ cert.get_status_display }}
                                    </span>
                                {% endif %}
                            </td>
                            <td>
                                {% if cert.certificate_url %}
                                    <a href="{{ cert.certificate_url }}" target="_blank" 
                                       class="btn btn-sm btn-primary">
                                        <i class="fas fa-download me-1"></i>Download
                                    </a>
                                {% else %}
                                    <button class="btn btn-sm btn-secondary" disabled>
                                        <i class="fas fa-hourglass-half me-1"></i>Pending
                                    </button>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="text-center py-5">
                <i class="fas fa-certificate fa-4x text-muted mb-3"></i>
                <h5 class="text-muted mb-2">No certifications recorded</h5>
                <p class="text-muted mb-4">
                    Complete training courses to earn certificates
                </p>
                <a href="{% url 'dashboard:training_catalog' %}" class="btn btn-primary">
                    <i class="fas fa-search me-2"></i>Browse Courses
                </a>
            </div>
        {% endif %}
    </div>
</div>

{% if user.is_superuser %}
<!-- Admin: All Certificates -->
<div class="card mt-4">
    <div class="card-header">
        <h5 class="mb-0">All Certificates (Admin View)</h5>
    </div>
    <div class="card-body">
        <p class="text-muted">
            <i class="fas fa-info-circle me-2"></i>
            As an admin, you can see all certificates in the system.
        </p>
    </div>
</div>
{% endif %}

{% endblock %}
```

---

### 3. Reports Dashboard (US-03)

**Current Issue:** No template exists for reports

#### Create `templates/dashboard/reports.html`

```html
{% extends 'dashboard/base_dashboard.html' %}
{% load static %}

{% block title %}Reports & Analytics - ProTrack{% endblock %}

{% block extra_css %}
<style>
.stat-card {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    height: 100%;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1f2937;
}

.stat-label {
    color: #6b7280;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

.chart-card {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}
</style>
{% endblock %}

{% block content %}
<div class="mb-4">
    <h2 class="mb-1">
        <i class="fas fa-chart-bar me-2" style="color: #3b82f6;"></i>
        Reports & Analytics
    </h2>
    <p class="text-muted mb-0">Track training completion and analyze overall performance</p>
</div>

<!-- Overall Statistics -->
<div class="row g-4 mb-4">
    <div class="col-md-3">
        <div class="stat-card">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="stat-label mb-2">Total Courses</div>
                    <div class="stat-value">{{ total_courses }}</div>
                    <small class="text-success">
                        <i class="fas fa-arrow-up me-1"></i>
                        {{ active_courses }} active
                    </small>
                </div>
                <div class="stat-icon" style="background: rgba(59,130,246,0.1); color: #3b82f6;">
                    <i class="fas fa-book"></i>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="stat-card">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="stat-label mb-2">Total Enrollments</div>
                    <div class="stat-value">{{ total_enrollments }}</div>
                    <small class="text-primary">
                        <i class="fas fa-users me-1"></i>
                        {{ active_enrollments }} active
                    </small>
                </div>
                <div class="stat-icon" style="background: rgba(16,185,129,0.1); color: #10b981;">
                    <i class="fas fa-user-graduate"></i>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="stat-card">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="stat-label mb-2">Completion Rate</div>
                    <div class="stat-value">{{ overall_completion_rate }}%</div>
                    <small class="text-success">
                        <i class="fas fa-check-circle me-1"></i>
                        {{ completed_enrollments }} completed
                    </small>
                </div>
                <div class="stat-icon" style="background: rgba(245,158,11,0.1); color: #f59e0b;">
                    <i class="fas fa-chart-line"></i>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="stat-card">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="stat-label mb-2">Average Score</div>
                    <div class="stat-value">{{ avg_score }}%</div>
                    <small class="text-info">
                        <i class="fas fa-star me-1"></i>
                        {{ total_certificates }} certificates
                    </small>
                </div>
                <div class="stat-icon" style="background: rgba(139,92,246,0.1); color: #8b5cf6;">
                    <i class="fas fa-award"></i>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Course Performance -->
<div class="chart-card">
    <h5 class="mb-4">
        <i class="fas fa-trophy me-2"></i>Top Performing Courses
    </h5>
    <div class="table-responsive">
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>Course</th>
                    <th>Enrolled</th>
                    <th>Completed</th>
                    <th>Avg Score</th>
                    <th>Completion Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for course in course_stats %}
                <tr>
                    <td><strong>{{ course.title }}</strong></td>
                    <td>{{ course.total_enrolled }}</td>
                    <td>{{ course.completed }}</td>
                    <td>
                        {% if course.avg_score %}
                            {{ course.avg_score|floatformat:1 }}%
                        {% else %}
                            <span class="text-muted">N/A</span>
                        {% endif %}
                    </td>
                    <td>
                        {% widthratio course.completed course.total_enrolled 100 %}%
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        No course data available
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- User Progress -->
<div class="chart-card">
    <h5 class="mb-4">
        <i class="fas fa-users me-2"></i>Top Learners
    </h5>
    <div class="table-responsive">
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Total Enrolled</th>
                    <th>Completed</th>
                    <th>In Progress</th>
                    <th>Avg Score</th>
                </tr>
            </thead>
            <tbody>
                {% for user_stat in user_progress %}
                <tr>
                    <td><strong>{{ user_stat.username }}</strong></td>
                    <td>{{ user_stat.total_enrollments }}</td>
                    <td>{{ user_stat.completed_courses }}</td>
                    <td>{{ user_stat.in_progress }}</td>
                    <td>
                        {% if user_stat.avg_score %}
                            {{ user_stat.avg_score|floatformat:1 }}%
                        {% else %}
                            <span class="text-muted">N/A</span>
                        {% endif %}
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        No user data available
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- Recent Activity -->
<div class="row g-4">
    <div class="col-md-6">
        <div class="chart-card">
            <h5 class="mb-4">
                <i class="fas fa-clock me-2"></i>Recent Enrollments
            </h5>
            <div class="list-group">
                {% for enrollment in recent_enrollments %}
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>{{ enrollment.user.username }}</strong>
                            <br>
                            <small class="text-muted">{{ enrollment.course.title }}</small>
                        </div>
                        <small class="text-muted">
                            {{ enrollment.enrolled_date|date:"M d, Y" }}
                        </small>
                    </div>
                </div>
                {% empty %}
                <p class="text-muted mb-0">No recent enrollments</p>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="chart-card">
            <h5 class="mb-4">
                <i class="fas fa-check-circle me-2"></i>Recent Completions
            </h5>
            <div class="list-group">
                {% for enrollment in recent_completions %}
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>{{ enrollment.user.username }}</strong>
                            <br>
                            <small class="text-muted">{{ enrollment.course.title }}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-success">{{ enrollment.score }}%</span>
                            <br>
                            <small class="text-muted">
                                {{ enrollment.completion_date|date:"M d, Y" }}
                            </small>
                        </div>
                    </div>
                </div>
                {% empty %}
                <p class="text-muted mb-0">No recent completions</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

{% endblock %}
```

---

## Quick Implementation Checklist

### Step 1: Update Templates
- [ ] Add materials section to `course_detail.html`
- [ ] Add materials to `my_training.html`
- [ ] Update `certifications.html` with new content
- [ ] Create `reports.html` template

### Step 2: Test Each Feature
- [ ] Upload a test material in Django Admin
- [ ] Create a test certificate
- [ ] Visit Reports page
- [ ] Check My Training shows materials

### Step 3: Create Test Data
```bash
python manage.py shell
```

```python
from dashboard.models import *
from accounts.models import CustomUser
from django.utils import timezone

# Get or create user
user = CustomUser.objects.first()

# Get or create course
course = TrainingCourse.objects.first()

# Create enrollment
enrollment = Enrollment.objects.create(
    user=user,
    course=course,
    status='completed',
    progress_percentage=100,
    score=85.5,
    completion_date=timezone.now().date()
)

# Create certificate
cert = Certificate.objects.create(
    enrollment=enrollment,
    certificate_number=f"CERT-2025-{enrollment.id:04d}",
    status='issued',
    issued_by=CustomUser.objects.filter(is_superuser=True).first()
)

print("✅ Test data created!")
```

---

## Summary

Your templates are **beautifully designed** ✨

What you need to do:
1. **Copy the HTML snippets above** into your templates
2. **Create the reports.html** template
3. **Test with real data**

All the backend is ready - just connect the frontend! 🚀
