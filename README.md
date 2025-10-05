# ProTrack - Professional Tracking System

A modern Django application for employee/student tracking with Supabase database integration and Google OAuth authentication.

## 🚀 Features

- **Modern UI/UX** with gradient designs and smooth animations
- **Supabase Database** integration for scalable data storage
- **Google OAuth** authentication with email verification
- **User Management** with different user types (Student, Employee, Admin)
- **Profile Management** with verification badges
- **Dashboard** with sidebar navigation
- **Responsive Design** for all devices

## 🛠️ Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd ProTrack
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your actual values:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Supabase Database Configuration
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-actual-supabase-password
DB_HOST=your-project-ref.supabase.co
DB_PORT=5432

# Email Configuration (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 3. Get Supabase Credentials

1. Go to [supabase.com](https://supabase.com/)
2. Create a new project or select existing project
3. Go to **Settings** → **Database**
4. Copy your connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.your-project-ref.supabase.co:5432/postgres
   ```
5. Extract and update these values in `.env`:
   - `DB_HOST`: `your-project-ref.supabase.co` (without `db.`)
   - `DB_PASSWORD`: Your actual password

### 4. Setup Google OAuth (Optional)

For Google authentication:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google People API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`
7. Copy **Client ID** and **Client Secret**

### 5. Configure in Django Admin

1. Run migrations:
```bash
python manage.py migrate
```

2. Create superuser:
```bash
python manage.py createsuperuser
```

3. Start the server:
```bash
python manage.py runserver
```

4. Go to `http://127.0.0.1:8000/admin/`

5. Configure Google OAuth (if using):
   - Go to **Social applications** → **Add social application**
   - Provider: **Google**
   - Name: **Google OAuth***
   - Client ID: [from Google Cloud Console]
   - Secret key: [from Google Cloud Console]
   - Sites: Select `127.0.0.1:8000`

### 6. Run the Application

Visit: `http://127.0.0.1:8000/`

## 📂 Project Structure

```
ProTrack/
├── accounts/           # User authentication and profiles
├── dashboard/          # Main dashboard and features
├── templates/          # HTML templates with modern UI
├── static/            # CSS, JS, images
├── protrack/          # Main Django project settings
└── requirements.txt   # Python dependencies
```

## 📱 Screenshots

The application features:
- Beautiful gradient login/register pages
- Modern dashboard with sidebar navigation
- Profile pages with email verification badges
- Responsive design for mobile and desktop

## 🔧 Development

### Key Files

- `accounts/models.py` - Custom user model with verification
- `templates/accounts/` - Modern login/register UI
- `protrack/settings.py` - Supabase and OAuth configuration
- `.env.example` - Template for environment variables

## 🚀 Deployment

For production deployment:

1. Update `DEBUG=False` in `.env`
2. Set up a production database
3. Configure proper SECRET_KEY
4. Set up static files serving
5. Configure email backend for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
