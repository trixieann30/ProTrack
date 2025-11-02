from django.core.management.base import BaseCommand
from dashboard.models import TrainingCategory, TrainingCourse
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create sample training courses for testing'

    def handle(self, *args, **kwargs):
        # Get or create admin user
        admin = CustomUser.objects.filter(is_superuser=True).first()

        # Create categories
        self.stdout.write("Creating categories...")
        tech_cat, _ = TrainingCategory.objects.get_or_create(
            name="Technical Skills",
            defaults={'description': 'Technical and IT courses', 'icon': 'fa-laptop-code'}
        )

        business_cat, _ = TrainingCategory.objects.get_or_create(
            name="Business Skills",
            defaults={'description': 'Business and management courses', 'icon': 'fa-briefcase'}
        )

        design_cat, _ = TrainingCategory.objects.get_or_create(
            name="Design & Architecture",
            defaults={'description': 'Design and architecture courses', 'icon': 'fa-drafting-compass'}
        )

        soft_cat, _ = TrainingCategory.objects.get_or_create(
            name="Soft Skills",
            defaults={'description': 'Communication and soft skills', 'icon': 'fa-users'}
        )

        self.stdout.write(self.style.SUCCESS(f'Created {TrainingCategory.objects.count()} categories'))

        # Create courses
        self.stdout.write("\nCreating courses...")

        courses_data = [
            # BSIT/BSCS Courses
            {
                'title': 'Python Programming Fundamentals',
                'description': 'Learn Python programming from scratch.',
                'category': tech_cat,
                'target_programs': 'BSIT,BSCS',
                'instructor': 'Dr. John Smith',
                'duration_hours': 40,
                'level': 'beginner',
                'learning_outcomes': 'Understand Python syntax, write basic programs',
                'prerequisites': 'Basic computer knowledge',
            },
            {
                'title': 'Web Development with Django',
                'description': 'Build modern web applications using Django.',
                'category': tech_cat,
                'target_programs': 'BSIT,BSCS',
                'instructor': 'Prof. Sarah Johnson',
                'duration_hours': 60,
                'level': 'intermediate',
                'learning_outcomes': 'Build full-stack web applications',
                'prerequisites': 'Python knowledge',
            },
            # BSARCH Course
            {
                'title': 'AutoCAD Fundamentals',
                'description': 'Learn 2D and 3D drafting using AutoCAD.',
                'category': design_cat,
                'target_programs': 'BSARCH',
                'instructor': 'Arch. Maria Garcia',
                'duration_hours': 45,
                'level': 'beginner',
                'learning_outcomes': 'Create 2D drawings, design 3D models',
                'prerequisites': 'Basic computer skills',
            },
            # BSCE Course
            {
                'title': 'Structural Design Principles',
                'description': 'Understand structural analysis and design.',
                'category': design_cat,
                'target_programs': 'BSARCH,BSCE',
                'instructor': 'Engr. Robert Lee',
                'duration_hours': 50,
                'level': 'advanced',
                'learning_outcomes': 'Analyze structural loads, design safe structures',
                'prerequisites': 'Engineering mathematics',
            },
            # BSBA Course
            {
                'title': 'Business Management Essentials',
                'description': 'Learn core business management principles.',
                'category': business_cat,
                'target_programs': 'BSBA',
                'instructor': 'Prof. Emily Davis',
                'duration_hours': 30,
                'level': 'beginner',
                'learning_outcomes': 'Understand management functions, develop business plans',
                'prerequisites': 'None',
            },
            # ALL Programs
            {
                'title': 'Effective Communication Skills',
                'description': 'Develop professional communication skills.',
                'category': soft_cat,
                'target_programs': 'ALL',
                'instructor': 'Dr. Lisa Brown',
                'duration_hours': 20,
                'level': 'beginner',
                'learning_outcomes': 'Communicate effectively, deliver presentations',
                'prerequisites': 'None',
            },
            {
                'title': 'Project Management Fundamentals',
                'description': 'Learn project management methodologies.',
                'category': business_cat,
                'target_programs': 'ALL',
                'instructor': 'PMP John Martinez',
                'duration_hours': 35,
                'level': 'intermediate',
                'learning_outcomes': 'Plan projects, manage resources, track progress',
                'prerequisites': 'Basic business knowledge',
            },
        ]

        created_count = 0
        for course_data in courses_data:
            course, created = TrainingCourse.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    **course_data,
                    'status': 'active',
                    'max_participants': 30,
                    'created_by': admin
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {course.title}'))
            else:
                self.stdout.write(f'Already exists: {course.title}')

        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'   Total courses: {TrainingCourse.objects.count()}')
        self.stdout.write(f'   Active courses: {TrainingCourse.objects.filter(status="active").count()}')
        self.stdout.write(f'   Newly created: {created_count}')
        self.stdout.write(self.style.SUCCESS('\nDone! Refresh your Training Catalog page.'))
