from django import forms
from .models import TrainingCourse

class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = [
            'title',
            'description',
            'category',
            'level',
            'duration_hours',
            'status',
            'target_programs',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

