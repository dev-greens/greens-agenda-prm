from django.conf import settings
def add_event_to_google_calendar(title, start, end, description=''):
    if getattr(settings, 'GOOGLE_CALENDAR_SYNC', False):
        print('Enviar para Google Calendar:', title, start, end)
    return None
