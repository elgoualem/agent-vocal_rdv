from calendar_service import get_service
from datetime import datetime, timedelta
import pytz

service = get_service()
tz = pytz.timezone('Europe/Paris')
now = datetime.now(tz)
end = now + timedelta(days=7)

events = service.events().list(
    calendarId='primary',
    timeMin=now.isoformat(),
    timeMax=end.isoformat(),
    maxResults=10,
    singleEvents=True,
    orderBy='startTime'
).execute()

print(f'Evenements trouves : {len(events.get("items", []))}')
for event in events.get('items', []):
    start = event['start'].get('dateTime', event['start'].get('date'))
    summary = event.get('summary', 'Sans titre')
    print(f'  - {summary} : {start}')
