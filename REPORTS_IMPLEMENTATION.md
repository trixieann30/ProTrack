# Reports Dashboard Implementation (US-03)

## Overview
The Reports dashboard provides comprehensive analytics and tracking for training completion and overall performance.

---

## URL
`/dashboard/reports/`

**Access:** Admin only (requires superuser)

---

## Features Implemented

### 1. Overall Statistics

#### Course Statistics
- **Total Courses**: All courses in the system
- **Active Courses**: Currently available courses
- **Archived Courses**: Old/completed courses

#### Enrollment Statistics
- **Total Enrollments**: All time enrollments
- **Active Enrollments**: Currently enrolled or in progress
- **Completed Enrollments**: Successfully completed

#### User Statistics
- **Total Users**: Non-admin users in system
- **Total Certificates**: Issued certificates
- **Overall Completion Rate**: Percentage of completed enrollments
- **Average Score**: Average score across all completed courses

---

### 2. Course Performance Analysis

**Top 10 Courses by Enrollment**

For each course:
- Course title
- Total enrolled users
- Completed enrollments
- Average score
- Completion rate

**Data Structure:**
```python
course_stats = [
    {
        'title': 'Python Programming',
        'total_enrolled': 50,
        'completed': 35,
        'avg_score': 85.5
    },
    ...
]
```

---

### 3. Recent Activity

#### Recent Enrollments
- Last 10 enrollments
- Shows: User, Course, Date enrolled, Status

#### Recent Completions
- Last 10 completed courses
- Shows: User, Course, Completion date, Score

---

### 4. User Progress Summary

**Top 10 Users by Completion**

For each user:
- Username
- Total enrollments
- Completed courses
- In progress courses
- Average score

**Data Structure:**
```python
user_progress = [
    {
        'username': 'john_doe',
        'total_enrollments': 10,
        'completed_courses': 7,
        'in_progress': 2,
        'avg_score': 88.5
    },
    ...
]
```

---

### 5. Enrollment Trends

**Monthly Enrollment Data (Last 6 Months)**

Shows enrollment trends over time:
```python
monthly_enrollments = [
    {'month': '2024-06', 'count': 25},
    {'month': '2024-07', 'count': 30},
    {'month': '2024-08', 'count': 28},
    ...
]
```

**Use for:**
- Line charts
- Trend analysis
- Growth tracking

---

### 6. Category Performance

**Performance by Training Category**

For each category:
- Category name
- Number of courses
- Total enrollments
- Completed enrollments
- Completion rate

**Data Structure:**
```python
category_stats = [
    {
        'name': 'Technical Skills',
        'course_count': 15,
        'enrollment_count': 200,
        'completion_count': 150
    },
    ...
]
```

---

### 7. Certificate Analytics

**Certificates Issued by Month (Last 6 Months)**

Tracks certificate issuance:
```python
certificates_by_month = [
    {'month': '2024-06', 'count': 15},
    {'month': '2024-07', 'count': 20},
    ...
]
```

---

## Context Variables Available in Template

### Overall Statistics
```python
{
    'total_courses': 50,
    'active_courses': 35,
    'archived_courses': 15,
    'total_enrollments': 500,
    'active_enrollments': 200,
    'completed_enrollments': 250,
    'total_users': 100,
    'total_certificates': 180,
    'overall_completion_rate': 50.0,
    'avg_score': 82.5,
}
```

### Detailed Analytics
```python
{
    'course_stats': QuerySet,           # Top 10 courses
    'recent_enrollments': QuerySet,     # Last 10 enrollments
    'recent_completions': QuerySet,     # Last 10 completions
    'user_progress': QuerySet,          # Top 10 users
    'monthly_enrollments': List,        # 6 months trend
    'category_stats': QuerySet,         # Category performance
    'certificates_by_month': List,      # 6 months certificates
}
```

---

## Template Structure (Suggested)

### `dashboard/reports.html`

```html
{% extends 'base.html' %}

{% block content %}
<div class="reports-dashboard">
    <!-- Header -->
    <div class="page-header">
        <h1>📊 Reports & Analytics</h1>
        <p>Track training completion and analyze overall performance</p>
    </div>

    <!-- Overall Statistics Cards -->
    <div class="stats-grid">
        <div class="stat-card">
            <h3>{{ total_courses }}</h3>
            <p>Total Courses</p>
            <small>{{ active_courses }} active</small>
        </div>
        
        <div class="stat-card">
            <h3>{{ total_enrollments }}</h3>
            <p>Total Enrollments</p>
            <small>{{ active_enrollments }} active</small>
        </div>
        
        <div class="stat-card">
            <h3>{{ overall_completion_rate }}%</h3>
            <p>Completion Rate</p>
            <small>{{ completed_enrollments }} completed</small>
        </div>
        
        <div class="stat-card">
            <h3>{{ avg_score }}%</h3>
            <p>Average Score</p>
            <small>Across all courses</small>
        </div>
        
        <div class="stat-card">
            <h3>{{ total_certificates }}</h3>
            <p>Certificates Issued</p>
        </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-section">
        <!-- Enrollment Trend Chart -->
        <div class="chart-card">
            <h2>Enrollment Trend (6 Months)</h2>
            <canvas id="enrollmentChart"></canvas>
        </div>
        
        <!-- Certificate Trend Chart -->
        <div class="chart-card">
            <h2>Certificates Issued (6 Months)</h2>
            <canvas id="certificateChart"></canvas>
        </div>
    </div>

    <!-- Course Performance Table -->
    <div class="table-section">
        <h2>Top Performing Courses</h2>
        <table class="data-table">
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
                    <td>{{ course.title }}</td>
                    <td>{{ course.total_enrolled }}</td>
                    <td>{{ course.completed }}</td>
                    <td>{{ course.avg_score|floatformat:1 }}%</td>
                    <td>
                        {% widthratio course.completed course.total_enrolled 100 %}%
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- User Progress Table -->
    <div class="table-section">
        <h2>Top Learners</h2>
        <table class="data-table">
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
                {% for user in user_progress %}
                <tr>
                    <td>{{ user.username }}</td>
                    <td>{{ user.total_enrollments }}</td>
                    <td>{{ user.completed_courses }}</td>
                    <td>{{ user.in_progress }}</td>
                    <td>{{ user.avg_score|floatformat:1 }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Category Performance -->
    <div class="table-section">
        <h2>Performance by Category</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Courses</th>
                    <th>Enrollments</th>
                    <th>Completions</th>
                    <th>Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for cat in category_stats %}
                <tr>
                    <td>{{ cat.name }}</td>
                    <td>{{ cat.course_count }}</td>
                    <td>{{ cat.enrollment_count }}</td>
                    <td>{{ cat.completion_count }}</td>
                    <td>
                        {% if cat.enrollment_count > 0 %}
                            {% widthratio cat.completion_count cat.enrollment_count 100 %}%
                        {% else %}
                            0%
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Recent Activity -->
    <div class="activity-section">
        <div class="activity-column">
            <h2>Recent Enrollments</h2>
            <ul class="activity-list">
                {% for enrollment in recent_enrollments %}
                <li>
                    <strong>{{ enrollment.user.username }}</strong>
                    enrolled in
                    <strong>{{ enrollment.course.title }}</strong>
                    <small>{{ enrollment.enrolled_date|date:"M d, Y" }}</small>
                </li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="activity-column">
            <h2>Recent Completions</h2>
            <ul class="activity-list">
                {% for enrollment in recent_completions %}
                <li>
                    <strong>{{ enrollment.user.username }}</strong>
                    completed
                    <strong>{{ enrollment.course.title }}</strong>
                    <small>Score: {{ enrollment.score }}%</small>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>

<!-- Chart.js for visualizations -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Enrollment Trend Chart
    const enrollmentCtx = document.getElementById('enrollmentChart').getContext('2d');
    new Chart(enrollmentCtx, {
        type: 'line',
        data: {
            labels: {{ monthly_enrollments|safe }}.map(d => d.month),
            datasets: [{
                label: 'Enrollments',
                data: {{ monthly_enrollments|safe }}.map(d => d.count),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        }
    });

    // Certificate Trend Chart
    const certCtx = document.getElementById('certificateChart').getContext('2d');
    new Chart(certCtx, {
        type: 'bar',
        data: {
            labels: {{ certificates_by_month|safe }}.map(d => d.month),
            datasets: [{
                label: 'Certificates',
                data: {{ certificates_by_month|safe }}.map(d => d.count),
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgb(153, 102, 255)',
                borderWidth: 1
            }]
        }
    });
</script>
{% endblock %}
```

---

## Export Functionality (Future Enhancement)

### CSV Export
Add export buttons to download reports as CSV:

```python
# In views.py
import csv
from django.http import HttpResponse

@login_required
@user_passes_test(is_superuser)
def export_course_report(request):
    """Export course performance to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="course_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Course', 'Enrolled', 'Completed', 'Avg Score', 'Completion Rate'])
    
    course_stats = TrainingCourse.objects.annotate(
        total_enrolled=Count('enrollments'),
        completed=Count('enrollments', filter=Q(enrollments__status='completed')),
        avg_score=Avg('enrollments__score')
    ).filter(total_enrolled__gt=0)
    
    for course in course_stats:
        completion_rate = (course.completed / course.total_enrolled * 100) if course.total_enrolled > 0 else 0
        writer.writerow([
            course.title,
            course.total_enrolled,
            course.completed,
            round(course.avg_score or 0, 1),
            round(completion_rate, 1)
        ])
    
    return response
```

### PDF Export
Use ReportLab to generate PDF reports:

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required
@user_passes_test(is_superuser)
def export_pdf_report(request):
    """Export analytics report as PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="training_report.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    # Add report content
    p.drawString(100, 750, "ProTrack Training Report")
    # ... add more content
    p.showPage()
    p.save()
    
    return response
```

---

## Testing the Reports View

### 1. Create Test Data

```python
python manage.py shell
```

```python
from dashboard.models import *
from accounts.models import CustomUser
from django.utils import timezone

# Create users
user1 = CustomUser.objects.create_user('learner1', 'learner1@test.com', 'password')
user2 = CustomUser.objects.create_user('learner2', 'learner2@test.com', 'password')

# Create category
cat = TrainingCategory.objects.create(name="Technical Skills")

# Create courses
course1 = TrainingCourse.objects.create(
    title="Python Basics",
    description="Learn Python",
    category=cat,
    instructor="John Doe",
    duration_hours=40,
    level="beginner",
    learning_outcomes="Python fundamentals",
    status="active"
)

# Create enrollments
Enrollment.objects.create(
    user=user1,
    course=course1,
    status="completed",
    progress_percentage=100,
    score=85.5,
    completion_date=timezone.now().date()
)

Enrollment.objects.create(
    user=user2,
    course=course1,
    status="in_progress",
    progress_percentage=60
)

print("✅ Test data created!")
```

### 2. Access Reports

1. Login as admin
2. Go to: `http://127.0.0.1:8000/dashboard/reports/`
3. Should see all statistics populated

---

## Summary

✅ **Reports View Created** - `/dashboard/reports/`  
✅ **Admin Only Access** - Requires superuser  
✅ **Comprehensive Analytics** - 7 different report sections  
✅ **Real-time Data** - Pulls from database  
✅ **User Story US-03** - Complete implementation  

**Next Steps:**
1. Create `dashboard/reports.html` template
2. Add charts using Chart.js
3. Add export functionality (CSV/PDF)
4. Add date range filters
5. Add more detailed drill-down views
