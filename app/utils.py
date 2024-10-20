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
        # Determine the year to use
        year = today.year
        # Handle leap year for February 29
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%m-%d").replace(year=year)
        except ValueError:
            logging.error(f"Invalid start_date '{start_date_str}' for year {year}. Adjusting to 02-28.")
            start_date = datetime.datetime.strptime("02-28", "%m-%d").replace(year=year)

        try:
            end_date = datetime.datetime.strptime(end_date_str, "%m-%d").replace(year=year)
        except ValueError:
            logging.error(f"Invalid end_date '{end_date_str}' for year {year}. Adjusting to 02-28.")
            end_date = datetime.datetime.strptime("02-28", "%m-%d").replace(year=year)

        # Handle ranges that span over the end of the year
        if end_date < start_date:
            end_date = end_date.replace(year=year + 1)

        return start_date <= today <= end_date
    except Exception as e:
        logging.error(f"Error parsing dates '{start_date_str}' - '{end_date_str}': {e}")
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

def check_overlapping_holidays(new_holidays):
    """
    Check if any holidays in new_holidays have overlapping date ranges.

    Args:
        new_holidays (list): List of holiday dicts with 'name', 'start_date', 'end_date'

    Returns:
        bool: True if overlaps exist, False otherwise
        list: List of tuples indicating overlapping holiday names
    """
    date_ranges = []
    overlaps = []

    today = datetime.datetime.now()
    year = today.year

    for holiday in new_holidays:
        name = holiday['name']
        start_str = holiday['start_date']
        end_str = holiday['end_date']

        try:
            start_date = datetime.datetime.strptime(start_str, "%m-%d").replace(year=year)
        except ValueError as e:
            logging.error(f"Invalid start_date '{start_str}' for holiday '{name}': {e}")
            raise ValueError(f"Invalid start_date '{start_str}' for holiday '{name}'.")

        try:
            end_date = datetime.datetime.strptime(end_str, "%m-%d").replace(year=year)
        except ValueError as e:
            # Handle February 29
            if start_date.month == 2 and start_date.day == 29:
                end_date = datetime.datetime.strptime("02-28", "%m-%d").replace(year=year)
            else:
                logging.error(f"Invalid end_date '{end_str}' for holiday '{name}': {e}")
                raise ValueError(f"Invalid end_date '{end_str}' for holiday '{name}'.")

        # If end_date is earlier than start_date, assume it spans to next year
        if end_date < start_date:
            end_date = end_date.replace(year=year + 1)

        date_ranges.append({
            'name': name,
            'start_date': start_date,
            'end_date': end_date
        })

    # Sort date_ranges by start_date
    date_ranges.sort(key=lambda x: x['start_date'])

    # Check for overlaps
    for i in range(1, len(date_ranges)):
        prev = date_ranges[i-1]
        current = date_ranges[i]
        if current['start_date'] <= prev['end_date']:
            overlaps.append((prev['name'], current['name']))

    if overlaps:
        return True, overlaps
    else:
        return False, []
