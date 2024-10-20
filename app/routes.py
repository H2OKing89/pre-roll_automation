from flask import render_template, request, redirect, url_for, flash
from . import create_app
import json
import os
from .utils import update_plex_preroll
from .scheduler import check_and_update_preroll

app = create_app()

@app.route('/')
def index():
    with open(os.path.join('config', 'holidays.json')) as f:
        holidays = json.load(f)['holidays']
    return render_template('index.html', holidays=holidays)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        # Handle form submission to update holidays
        new_holidays = request.form.get('holidays')
        try:
            holidays_data = json.loads(new_holidays)
            with open(os.path.join('config', 'holidays.json'), 'w') as f:
                json.dump({"holidays": holidays_data}, f, indent=4)
            flash('Holiday schedule updated successfully!', 'success')
            # Optionally trigger immediate update
            check_and_update_preroll()
        except json.JSONDecodeError:
            flash('Invalid JSON format!', 'danger')
        return redirect(url_for('index'))
    
    with open(os.path.join('config', 'holidays.json')) as f:
        holidays = json.load(f)['holidays']
    return render_template('edit.html', holidays=holidays)
