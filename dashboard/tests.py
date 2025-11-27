import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import TrainingCourse, Enrollment, TrainingCategory

User = get_user_model()

class CalendarFunctionalityTests(TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        self.category = TrainingCategory.objects.create(name='Test Category')
        self.course = TrainingCourse.objects.create(
            title='Test Course',
            description='A course for testing.',
            category=self.category,
            instructor='Test Instructor',
            duration_hours=10,
            learning_outcomes='Learn to test.',
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course, status='enrolled')

    def test_calendar_view_loads_successfully(self):
        """Test that the main calendar page loads correctly."""
        response = self.client.get(reverse('dashboard:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/calendar.html')

    def test_get_calendar_events_api_returns_data(self):
        """Test that the calendar events API returns a successful response with event data."""
        response = self.client.get(reverse('dashboard:calendar_events'))
        self.assertEqual(response.status_code, 200)
        
        events = response.json()
        self.assertIsInstance(events, list)
        self.assertTrue(len(events) > 0)
        
        # Check for the course title in the events
        self.assertTrue(any(self.course.title in event['title'] for event in events))

    def test_update_enrollment_completion_date_api(self):
        """Test that the API for updating the completion date works correctly."""
        new_completion_date = date.today() + timedelta(days=10)
        
        response = self.client.post(
            reverse('dashboard:update_enrollment_completion'),
            data=json.dumps({
                'id': self.enrollment.id,
                'completion_date': new_completion_date.strftime('%Y-%m-%d'),
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Verify the date was updated in the database
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.completion_date, new_completion_date)
