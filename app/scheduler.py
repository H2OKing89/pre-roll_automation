import json
import datetime
import os
from .utils import update_plex_preroll
import logging

def is_current_date_in_range(start_date_str, end_date_str):
    today = datetime.datetime.now()
    start_date = datetime.datetime.strptime(start_date_str, "%m-%d").replace(year=today.year)
    end_date = datetime.datetime.strptime(end_date_str, "%m-%d").replace(year=today.year)

    # Handle year change (e.g., December to January)
    if end_date < start_date:
        end_date = end_date.replace(year=end_date.year + 1)

    return start_date <= today <= end_date

def check_and_update_preroll():
    try:
        with open(os.path.join('config', 'holidays.json')) as f:
            holidays = json.load(f)['holidays']
        plex_token = os.getenv('PLEX_TOKEN')
        plex_base_url = os.getenv('PLEX_BASE_URL')
        for holiday in holidays:
            if is_current_date_in_range(holiday['start_date'], holiday['end_date']):
                update_plex_preroll(plex_token, plex_base_url, holiday['pre_roll'])
                return
        # If no holiday matches, clear pre-roll
        update_plex_preroll(plex_token, plex_base_url, '')
    except Exception as e:
        logging.error(f"Error in scheduler: {e}")
