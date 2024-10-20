# app/routes.py

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from functools import wraps
from .utils import (
    load_holidays,
    save_holidays,
    get_plex_settings,
    update_plex_settings,
    check_overlapping_holidays
)
import os

main = Blueprint('main', __name__, template_folder='../templates')

def check_auth(username, password):
    return username == os.getenv('WEB_GUI_USERNAME') and password == os.getenv('WEB_GUI_PASSWORD')

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to log in with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@main.route('/')
@requires_auth
def index():
    """Render the main dashboard displaying current holiday schedules and Plex settings."""
    holidays = load_holidays()
    plex_settings = get_plex_settings()
    return render_template('index.html', holidays=holidays, plex=plex_settings)

@main.route('/settings', methods=['GET', 'POST'])
@requires_auth
def settings():
    """Render and handle the form to edit Plex server settings."""
    plex_settings = get_plex_settings()

    if request.method == 'POST':
        base_url = request.form.get('base_url')
        token = request.form.get('token')

        if base_url and token:
            success = update_plex_settings(base_url, token)
            if success:
                flash('Plex settings updated successfully!', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Failed to update Plex settings.', 'danger')
        else:
            flash('Both Plex URL and Token are required.', 'danger')

    return render_template('settings.html', plex=plex_settings)

@main.route('/holidays', methods=['GET', 'POST'])
@requires_auth
def manage_holidays():
    """Render and handle the form to manage holiday schedules."""
    holidays = load_holidays()

    if request.method == 'POST':
        # Process form data to update holidays
        try:
            updated_holidays = []
            holiday_count = int(request.form.get('holiday_count', 0))
            for i in range(1, holiday_count + 1):
                name = request.form.get(f'holiday_name_{i}')
                start_date = request.form.get(f'holiday_start_{i}')
                end_date = request.form.get(f'holiday_end_{i}')
                pre_rolls_input = request.form.get(f'holiday_preroll_{i}')
                selection_mode = request.form.get(f'holiday_selection_mode_{i}', 'random')

                # Split pre-rolls by comma and strip whitespace
                pre_rolls = [pr.strip() for pr in pre_rolls_input.split(',') if pr.strip()]

                if name and start_date and end_date and pre_rolls:
                    updated_holidays.append({
                        'name': name,
                        'start_date': start_date,
                        'end_date': end_date,
                        'pre_rolls': pre_rolls,
                        'selection_mode': selection_mode,
                        'last_index': 0  # Initialize last_index
                    })

            # Initialize an empty list to collect all error messages
            error_messages = []

            # Validate each holiday's date format
            for holiday in updated_holidays:
                name = holiday['name']
                start_date = holiday['start_date']
                end_date = holiday['end_date']
                try:
                    datetime.datetime.strptime(start_date, "%m-%d")
                except ValueError:
                    error_messages.append(f"Invalid start date '{start_date}' for holiday '{name}'. Please use MM-DD format.")

                try:
                    datetime.datetime.strptime(end_date, "%m-%d")
                except ValueError:
                    error_messages.append(f"Invalid end date '{end_date}' for holiday '{name}'. Please use MM-DD format.")

            # Check for overlapping holidays only if no date format errors
            if not error_messages:
                overlaps_exist, overlapping_pairs = check_overlapping_holidays(updated_holidays)
                if overlaps_exist:
                    for pair in overlapping_pairs:
                        error_messages.append(f"Holiday '{pair[0]}' overlaps with holiday '{pair[1]}'.")

            # If there are errors, flash all of them and do not save
            if error_messages:
                for msg in error_messages:
                    flash(msg, 'danger')
                return redirect(url_for('main.manage_holidays'))

            # If no errors, save the holidays
            save_holidays(updated_holidays)
            flash('Holiday schedules updated successfully!', 'success')
            return redirect(url_for('main.index'))
        except ValueError as ve:
            flash(str(ve), 'danger')
            return redirect(url_for('main.manage_holidays'))
        except Exception as e:
            flash(f'Error updating holidays: {e}', 'danger')
            return redirect(url_for('main.manage_holidays'))

    return render_template('holidays.html', holidays=holidays)

# Optional: Add manual trigger for testing purposes
@main.route('/trigger', methods=['POST'])
@requires_auth
def trigger_update():
    """Manually trigger the pre-roll update."""
    try:
        from .utils import check_and_update_preroll
        check_and_update_preroll()
        flash('Pre-roll update triggered successfully!', 'success')
    except Exception as e:
        flash(f'Error triggering update: {e}', 'danger')
    return redirect(url_for('main.index'))
