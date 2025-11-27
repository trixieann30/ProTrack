import random
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from dashboard.models import TrainingCategory, TrainingCourse, TrainingMaterial

class Command(BaseCommand):
    help = 'Seeds the database with a variety of sample training courses.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with idempotent script...')
        self.create_categories_and_courses()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully with detailed courses!'))

    def create_categories_and_courses(self):
        # Technical Skills
        tech_cat, _ = TrainingCategory.objects.update_or_create(name='Technical Skills', defaults={'icon': 'fa-code'})
        self.create_course(
            category=tech_cat,
            title='Introduction to Python Programming',
            description='A beginner-friendly introduction to the Python programming language, covering fundamental concepts and practical applications.',
            instructor='Dr. Alan Turing',
            duration_hours=25.0,
            level='beginner',
            learning_outcomes='- Understand basic Python syntax and data structures.\n- Write simple scripts to automate tasks.\n- Learn object-oriented programming principles.',
            materials=[
                {'title': 'Syllabus and Course Overview', 'material_type': 'document'},
                {'title': 'Module 1: Python Basics', 'material_type': 'video'},
                {'title': 'Module 2: Data Structures', 'material_type': 'presentation'},
                {'title': 'Final Project: Web Scraper', 'material_type': 'quiz'},
            ]
        )
        self.create_course(
            category=tech_cat,
            title='Advanced Django Web Development',
            description='Master advanced concepts in Django, including the Django REST Framework, to build robust and scalable web applications.',
            instructor='Ada Lovelace',
            duration_hours=40.0,
            level='advanced',
            learning_outcomes='- Build complex web applications with Django.\n- Create powerful APIs using Django REST Framework.\n- Deploy Django projects to production environments.',
            materials=[
                {'title': 'Advanced Django Patterns', 'material_type': 'document'},
                {'title': 'Building a REST API', 'material_type': 'video'},
                {'title': 'Deployment Strategies', 'material_type': 'document'},
                {'title': 'Final Exam', 'material_type': 'quiz'},
            ]
        )

        # Soft Skills
        soft_skills_cat, _ = TrainingCategory.objects.update_or_create(name='Soft Skills', defaults={'icon': 'fa-comments'})
        self.create_course(
            category=soft_skills_cat,
            title='Effective Communication in the Workplace',
            description='Learn how to communicate effectively with colleagues, clients, and stakeholders to foster a collaborative and productive work environment.',
            instructor='Dale Carnegie',
            duration_hours=12.0,
            level='intermediate',
            learning_outcomes='- Improve presentation and public speaking skills.\n- Practice active listening and empathy.\n- Handle difficult conversations with confidence.',
            materials=[
                {'title': 'The Art of Communication', 'material_type': 'document'},
                {'title': 'Public Speaking Workshop', 'material_type': 'video'},
                {'title': 'Final Presentation', 'material_type': 'quiz'},
            ]
        )

        # Project Management
        pm_cat, _ = TrainingCategory.objects.update_or_create(name='Project Management', defaults={'icon': 'fa-tasks'})
        self.create_course(
            category=pm_cat,
            title='Agile and Scrum Fundamentals',
            description='An introduction to Agile methodologies and the Scrum framework for effective project management.',
            instructor='Jeff Sutherland',
            duration_hours=18.0,
            level='intermediate',
            learning_outcomes='- Understand the Agile Manifesto and principles.\n- Learn the roles, events, and artifacts of Scrum.\n- Apply Scrum to real-world projects.',
            materials=[
                {'title': 'The Scrum Guide', 'material_type': 'document'},
                {'title': 'Sprint Planning Simulation', 'material_type': 'video'},
                {'title': 'Scrum Master Certification Quiz', 'material_type': 'quiz'},
            ]
        )

        # Data Science
        data_sci_cat, _ = TrainingCategory.objects.update_or_create(name='Data Science', defaults={'icon': 'fa-database'})
        self.create_course(
            category=data_sci_cat,
            title='Data Analysis with Pandas',
            description='Learn how to use the Pandas library in Python for data manipulation and analysis.',
            instructor='Wes McKinney',
            duration_hours=22.0,
            level='intermediate',
            learning_outcomes='- Clean, transform, and merge datasets.\n- Perform time-series analysis.\n- Create data visualizations with Matplotlib.',
            materials=[
                {'title': 'Pandas Cookbook', 'material_type': 'document'},
                {'title': 'Data Wrangling Tutorial', 'material_type': 'video'},
                {'title': 'Final Analysis Project', 'material_type': 'quiz'},
            ]
        )

    def create_course(self, category, title, description, instructor, duration_hours, level, learning_outcomes, materials):
        course, created = TrainingCourse.objects.update_or_create(
            title=title,
            defaults={
                'category': category,
                'description': description,
                'instructor': instructor,
                'duration_hours': duration_hours,
                'level': level,
                'max_participants': random.randint(20, 50),
                'learning_outcomes': learning_outcomes,
            }
        )
        # Clear existing materials to ensure the list is always up-to-date
        course.materials.all().delete()
        for i, material_data in enumerate(materials):
            self.create_material(course, material_data, i)

    def create_material(self, course, material_data, order):
        file_name = f"{material_data['title'].replace(' ', '_').lower()}.pdf"
        TrainingMaterial.objects.create(
            course=course,
            title=material_data['title'],
            material_type=material_data.get('material_type', 'document'),
            file_url=f'https://example.com/{file_name}',
            file_name=file_name,
            file_size=random.randint(1000, 5000),
            order=order,
        )
