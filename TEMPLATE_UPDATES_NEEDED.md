# Template Updates to Implement User Stories

## ✅ Reports Page - FIXED!

The database error is now fixed. The Reports page will work with SQLite.

---

## 🔧 Templates That Need Updates

### 1. My Training - Add Materials Display (US-07)

**File:** `templates/dashboard/my_training.html`

**What to add:** Show training materials for each enrolled course

**Location:** Inside the training card, after the progress section (around line 271)

**Add this code:**

```html
<!-- Add after the progress-section div, before training-actions -->
{% if enrollment.course.materials.all %}
<div class="mt-3 pt-3" style="border-top: 1px solid #e5e7eb;">
    <h6 class="text-muted mb-2" style="font-size: 0.9rem;">
        <i class="fas fa-folder-open me-2"></i>Course Materials
    </h6>
    <div class="d-flex flex-wrap gap-2">
        {% for material in enrollment.course.materials.all|slice:":3" %}
        <a href="{{ material.file_url }}" target="_blank" 
           class="btn btn-sm btn-outline-primary" 
           title="{{ material.description }}">
            <i class="fas fa-file-{% if material.material_type == 'document' %}pdf{% elif material.material_type == 'video' %}video{% elif material.material_type == 'presentation' %}powerpoint{% else %}alt{% endif %} me-1"></i>
            {{ material.title|truncatewords:3 }}
            {% if material.is_required %}
            <span class="badge bg-danger ms-1" style="font-size: 0.65rem;">Required</span>
            {% endif %}
        </a>
        {% endfor %}
        {% if enrollment.course.materials.count > 3 %}
        <a href="{% url 'dashboard:course_detail' enrollment.course.id %}" 
           class="btn btn-sm btn-outline-secondary">
            <i class="fas fa-ellipsis-h me-1"></i>
            +{{ enrollment.course.materials.count|add:"-3" }} more
        </a>
        {% endif %}
    </div>
</div>
{% endif %}
```

---

### 2. Training Catalog - Show Material Count (US-05, US-07)

**File:** `templates/dashboard/training_catalog.html`

**What to add:** Show how many materials each course has

**Location:** Inside course-meta div (around line 264)

**Add this after the category meta-item:**

```html
<div class="course-meta-item">
    <i class="fas fa-folder"></i>
    {{ course.materials.count }} material{{ course.materials.count|pluralize }}
</div>
```

---

### 3. Certifications - Display Actual Certificates (US-09)

**File:** `templates/dashboard/certifications.html`

**Current issue:** Template exists but doesn't show real certificate data

**Solution:** The template I created earlier (`templates/dashboard/reports.html`) has the full implementation. 

Let me check the current certifications template:

<function_calls>
<invoke name="read_file">
<parameter name="file_path">c:\Users\Ethereal\ProTrack\templates\dashboard\certifications.html
