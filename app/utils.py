# app/utils.py

import json
import datetime
import requests
import os
import logging
import random
from dotenv import load_dotenv, set_key
import pytz

# Load environment variables from .env file
load_dotenv()

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def load_holidays():
    """Load holiday schedules from holidays.json."""
    try:
        with open('config/holidays.json') as f:
            data = json.load(f)
            return data.get('holidays', [])
    except Exception as e:
        logging.error(f"Error loading holidays.json: {e}")
        return []

def save_holidays(holidays):
    """Save holiday schedules to holidays.json."""
    try:
        with open('config/holidays.json', 'w') as f:
            json.dump({'holidays': holidays}, f, indent=4)
        logging.info("Holiday schedules saved successfully.")
    except Exception as e:
        logging.error(f"Error saving holidays.json: {e}")

def get_plex_settings():
    """Get Plex settings from environment variables."""
    return {
        'base_url': os.getenv('PLEX_BASE_URL'),
        'token': os.getenv('PLEX_TOKEN')
    }

def update_plex_settings(base_url, token):
    """Update Plex settings in the .env file and reload them."""
    try:
        dotenv_path = '.env'
        set_key(dotenv_path, 'PLEX_BASE_URL', base_url)
        set_key(dotenv_path, 'PLEX_TOKEN', token)
        # Reload environment variables
        load_dotenv(dotenv_path, override=True)
        logging.info("Plex settings updated successfully in .env.")
        return True
    except Exception as e:
        logging.error(f"Error updating Plex settings in .env: {e}")
        return False

def is_current_date_in_range(start_date_str, end_date_str):
    """
    Check if today's date is within the specified date range.

    Args:
        start_date_str (str): Start date in "MM-DD" format.
        end_date_str (str): End date in "MM-DD" format.

    Returns:
        bool: True if today is within the range, False otherwise.
    """
    today = datetime.datetime.now()
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%m-%d").replace(year=today.year)
        end_date = datetime.datetime.strptime(end_date_str, "%m-%d").replace(year=today.year)

        # Handle ranges that span over the end of the year
        if end_date < start_date:
            end_date = end_date.replace(year=today.year + 1)

        return start_date <= today <= end_date
    except Exception as e:
        logging.error(f"Error parsing dates: {e}")
        return False

def update_plex_preroll(pre_roll_path):
    """
    Update the Plex pre-roll setting via the Plex API.

    Args:
        pre_roll_path (str): The file path to the pre-roll video.
    """
    plex_settings = get_plex_settings()
    base_url = plex_settings.get('base_url')
    token = plex_settings.get('token')

    if not base_url or not token:
        logging.error("Plex base URL or token is not set.")
        return

    url = f"{base_url}/:/prefs?CinemaTrailersPrerollID={pre_roll_path}&X-Plex-Token={token}"
    try:
        response = requests.put(url)
        if response.status_code == 200:
            logging.info(f"Pre-roll updated successfully to: {pre_roll_path}")
        else:
            logging.error(f"Failed to update pre-roll: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"Error updating Plex pre-roll: {e}")

def select_sequential_preroll(holiday):
    """
    Select the next pre-roll in sequence for a holiday.

    Args:
        holiday (dict): Holiday configuration.

    Returns:
        str: Selected pre-roll path.
    """
    try:
        last_index = holiday.get('last_index', -1)
        next_index = (last_index + 1) % len(holiday['pre_rolls'])
        selected_pre_roll = holiday['pre_rolls'][next_index]

        # Update the last_index in holidays.json
        holidays = load_holidays()
        for h in holidays:
            if h['name'] == holiday['name']:
                h['last_index'] = next_index
                break
        save_holidays(holidays)

        return selected_pre_roll
    except Exception as e:
        logging.error(f"Error selecting sequential pre-roll for {holiday['name']}: {e}")
        return random.choice(holiday['pre_rolls'])  # Fallback to random selection

def check_and_update_preroll():
    """
    Check the current date against holiday schedules and update the Plex pre-roll accordingly.
    """
    holidays = load_holidays()
    for holiday in holidays:
        if is_current_date_in_range(holiday['start_date'], holiday['end_date']):
            pre_rolls = holiday.get('pre_rolls', [])
            selection_mode = holiday.get('selection_mode', 'random')

            if not pre_rolls:
                logging.warning(f"No pre-rolls defined for holiday: {holiday['name']}")
                continue

            if selection_mode == 'random':
                selected_pre_roll = random.choice(pre_rolls)
            elif selection_mode == 'sequential':
                selected_pre_roll = select_sequential_preroll(holiday)
            else:
                logging.error(f"Unknown selection mode '{selection_mode}' for holiday: {holiday['name']}")
                continue

            update_plex_preroll(selected_pre_roll)
            logging.info(f"Pre-roll set to {selected_pre_roll} for holiday: {holiday['name']}")
            return
    # Clear pre-roll if no holiday matches
    update_plex_preroll('')
    logging.info("No current holiday match. Pre-roll cleared.")
