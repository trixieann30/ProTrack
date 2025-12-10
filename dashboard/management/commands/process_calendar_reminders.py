from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from dashboard.models import CalendarEvent


class Command(BaseCommand):
    help = 'Process pending calendar reminders and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        self.stdout.write(self.style.NOTICE(f'\n{"="*60}'))
        self.stdout.write(self.style.NOTICE('Processing Calendar Reminders'))
        self.stdout.write(self.style.NOTICE(f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.NOTICE(f'{"="*60}\n'))
        
        # Get all events that haven't had their reminder sent yet
        pending_events = CalendarEvent.objects.filter(reminder_sent=False)
        
        if not pending_events.exists():
            self.stdout.write(self.style.WARNING('No pending reminders found.'))
            return
        
        self.stdout.write(f'Found {pending_events.count()} events with pending reminders\n')
        
        reminders_sent = 0
        reminders_skipped = 0
        
        for event in pending_events:
            reminder_time = event.get_reminder_datetime()
            event_datetime = timezone.make_aware(
                datetime.combine(event.event_date, event.event_time)
            )
            
            # Check if it's time to send the reminder
            if now >= reminder_time:
                # Don't send reminders for past events
                if event_datetime < now:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  SKIPPED (past): {event.title} - Event was at {event_datetime}'
                        )
                    )
                    # Mark as sent to avoid future processing
                    event.reminder_sent = True
                    event.save()
                    reminders_skipped += 1
                    continue
                
                self.stdout.write(
                    f'  Processing: {event.title} (User: {event.user.username})'
                )
                self.stdout.write(
                    f'    Event: {event_datetime.strftime("%Y-%m-%d %H:%M")}'
                )
                self.stdout.write(
                    f'    Reminder time: {reminder_time.strftime("%Y-%m-%d %H:%M")}'
                )
                
                if dry_run:
                    self.stdout.write(self.style.SUCCESS('    [DRY RUN] Would send reminder'))
                else:
                    result = event.create_reminder_notification()
                    if result:
                        self.stdout.write(self.style.SUCCESS('    ✅ Reminder sent!'))
                        reminders_sent += 1
                    else:
                        self.stdout.write(self.style.WARNING('    Already sent'))
            else:
                time_until = reminder_time - now
                self.stdout.write(
                    f'  PENDING: {event.title} - Reminder in {time_until}'
                )
        
        self.stdout.write(self.style.NOTICE(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS(f'Reminders sent: {reminders_sent}'))
        self.stdout.write(self.style.WARNING(f'Reminders skipped (past events): {reminders_skipped}'))
        self.stdout.write(self.style.NOTICE(f'{"="*60}\n'))
