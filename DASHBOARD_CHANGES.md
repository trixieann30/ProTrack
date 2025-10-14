# Dashboard Separation Changes

## Summary
Separated user and admin dashboards with role-based access control. Regular users (students and employees) can only register through the form, while administrators must be created via Django's `createsuperuser` command.

## Changes Made

### 1. Registration Form (`accounts/forms.py`)
- **Removed "Administrator" option** from registration form
- Only **Student** and **Employee** can register through the website
- Administrators can only be created via command line: `python manage.py createsuperuser`

### 2. Login Redirect Logic (`accounts/views.py`)
- Added `get_success_url()` method to `CustomLoginView`
- **Superusers** → redirected to `/dashboard/admin/`
- **Regular users** → redirected to `/dashboard/user/`
- Registration also redirects based on user type

### 3. Dashboard Views (`dashboard/views.py`)
Created three separate views:

#### `admin_dashboard()`
- **Access**: Only superusers (via `@user_passes_test(is_superuser)`)
- **Features**:
  - View all user statistics
  - See total users, students, employees, admins
  - View recent users table
  - Link to Django admin panel
- **Template**: `dashboard/admin_dashboard.html`

#### `user_dashboard()`
- **Access**: All logged-in users (students and employees)
- **Features**:
  - Personal statistics (training sessions, certifications, hours)
  - Progress tracking
  - Quick actions
  - Welcome banner with user's name
- **Template**: `dashboard/user_dashboard.html`

#### `dashboard()` (Router)
- Automatically redirects to appropriate dashboard based on user role

### 4. URL Configuration (`dashboard/urls.py`)
Added new URL patterns:
```python
path('', views.dashboard, name='dashboard'),           # Router
path('admin/', views.admin_dashboard, name='admin_dashboard'),
path('user/', views.user_dashboard, name='user_dashboard'),
```

### 5. Templates Created

#### `templates/dashboard/admin_dashboard.html`
- Admin badge indicator
- 4 stat cards: Total Users, Students, Employees, Administrators
- Recent users table with user details
- Link to Django admin panel

#### `templates/dashboard/user_dashboard.html`
- Welcome banner with personalized greeting
- 4 stat cards: Training Sessions, Certifications, Completed Hours, Profile Complete
- Progress chart placeholder
- Quick actions task list

## How to Use

### Creating an Administrator
```powershell
# In PowerShell terminal
python manage.py createsuperuser

# Follow prompts:
# Username: admin
# Email: admin@example.com
# Password: ********
```

### User Registration Flow
1. **Regular users** (students/employees):
   - Register at `/accounts/register/`
   - Choose "Student" or "Employee"
   - Auto-redirected to user dashboard

2. **Administrators**:
   - Created via `createsuperuser` command
   - Login at `/accounts/login/`
   - Auto-redirected to admin dashboard

### Access URLs
- **Admin Dashboard**: `http://127.0.0.1:8000/dashboard/admin/`
- **User Dashboard**: `http://127.0.0.1:8000/dashboard/user/`
- **Auto Router**: `http://127.0.0.1:8000/dashboard/`

## Security Features
- ✅ Admin dashboard protected by `@user_passes_test(is_superuser)`
- ✅ Regular users cannot access admin dashboard
- ✅ Superusers cannot be created through registration form
- ✅ Automatic role-based redirection
- ✅ Permission denied (403) if unauthorized access attempted

## Testing

### Test Admin Access
1. Create superuser: `python manage.py createsuperuser`
2. Login with superuser credentials
3. Should redirect to admin dashboard with all statistics

### Test User Access
1. Register new account (choose Student or Employee)
2. Should redirect to user dashboard with personal stats
3. Try accessing `/dashboard/admin/` - should get 403 Forbidden

## Next Steps
- Add actual training session data to user dashboard
- Implement certification tracking
- Add user management features to admin dashboard
- Create reports and analytics for administrators
