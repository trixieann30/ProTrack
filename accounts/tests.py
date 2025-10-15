from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, UserProfile

class RegistrationTestCase(TestCase):
    """Test user registration functionality"""
    
    def test_registration_page_loads(self):
        """Test that registration page loads successfully"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
    
    def test_registration_success_with_autologin(self):
        """Test successful registration with auto-login"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        
        # Check user was created
        self.assertEqual(CustomUser.objects.count(), 1)
        user = CustomUser.objects.first()
        self.assertEqual(user.username, 'testuser')
        
        # Check UserProfile was created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        # Check user is auto-logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Check redirect to dashboard
        self.assertRedirects(response, reverse('dashboard:dashboard'))
    
    def test_registration_invalid_data(self):
        """Test registration with invalid data"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'te',  # Too short
            'email': 'invalid-email',
            'password1': '123',  # Too weak
            'password2': '456',  # Doesn't match
        })
        
        # Should not create user
        self.assertEqual(CustomUser.objects.count(), 0)
        
        # Should stay on registration page
        self.assertEqual(response.status_code, 200)


class LoginTestCase(TestCase):
    """Test user login functionality"""
    
    def setUp(self):
        """Create a test user"""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!@#',
            user_type='student'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'TestPass123!@#',
        })
        
        # Check user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Check redirect to dashboard
        self.assertRedirects(response, reverse('dashboard:dashboard'))
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        
        # Should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)


class DashboardRBACTestCase(TestCase):
    """Test role-based access control in dashboard"""
    
    def setUp(self):
        """Create test users with different roles"""
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='AdminPass123!',
            user_type='admin'
        )
        self.student = CustomUser.objects.create_user(
            username='student',
            password='StudentPass123!',
            user_type='student'
        )
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='EmployeePass123!',
            user_type='employee'
        )
    
    def test_admin_sees_all_stats(self):
        """Test that admin can see all user statistics"""
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('dashboard:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['total_users'])
        self.assertIsNotNone(response.context['total_students'])
        self.assertIsNotNone(response.context['total_employees'])
    
    def test_student_sees_limited_stats(self):
        """Test that students see limited statistics"""
        self.client.login(username='student', password='StudentPass123!')
        response = self.client.get(reverse('dashboard:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['total_users'])
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:dashboard')}")


class ProfileManagementTestCase(TestCase):
    """Test profile viewing and editing"""
    
    def setUp(self):
        """Create a test user with profile"""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            user_type='student'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.login(username='testuser', password='TestPass123!')
    
    def test_profile_page_loads(self):
        """Test that profile page loads"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
    
    def test_edit_profile_page_loads(self):
        """Test that edit profile page loads"""
        response = self.client.get(reverse('accounts:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/edit_profile.html')
    
    def test_profile_update_success(self):
        """Test successful profile update"""
        response = self.client.post(reverse('accounts:edit_profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+1234567890',
            'department': 'IT',
            'position': 'Developer',
            'bio': 'Test bio',
            'skills': 'Python, Django',
            'certifications': 'AWS',
        })
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        # Check updates
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.profile.bio, 'Test bio')
        
        # Check redirect
        self.assertRedirects(response, reverse('accounts:profile'))