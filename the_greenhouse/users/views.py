from flask import render_template, url_for, flash, redirect, request, Blueprint, abort, session, current_app
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import select, desc, and_
from the_greenhouse import db
from the_greenhouse.models import User, Events, EventAttendee
from the_greenhouse.users.forms import RegisterForm, LoginForm, UpdateUserForm
from the_greenhouse.users.pfp_handler import add_profile_pic
from datetime import date
import calendar
import os

users = Blueprint('users', __name__)

@users.route('/logout')
def logout():
    print("Logging out")
    logout_user()
    return redirect(url_for('core.index'))

@users.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = User(email = form.email.data,
                    username = form.username.data,
                    password = form.password.data)
        
        db.session.add(user)
        db.session.commit()
        flash('Thanks for joining The Greenhouse!', 'success')
        return redirect(url_for('users.login'))
    
    else:
        # Show specific form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
    
    return render_template('register.html', form = form)

@users.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        
        user = db.session.execute(select(User).filter_by(email = form.email.data)).scalar_one_or_none()
        if user is not None:
            if user.check_password(form.password.data):
                login_user(user)
                flash('Log In Successful!', 'success')

                next = request.args.get('next')

                if next == None or not next[0] == '/':
                    next = url_for('core.index')

                return redirect(next)
            else:
                flash('Invalid email or password', 'error')
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html', form = form)

@users.route('/account', methods = ['GET', 'POST'])
@login_required
def account():
    # Get calendar month and year from request parameters
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    # Default to current month/year if not provided
    if not month or not year:
        today = date.today()
        month = today.month
        year = today.year
    
    # Ensure month is between 1-12
    month = max(1, min(12, month))
    
    # Get the first day of the month and calculate calendar data
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Get all events the user is attending in this month
    user_events = db.session.scalars(
        select(Events)
        .join(EventAttendee, Events.id == EventAttendee.event_id)
        .where(
            and_(
                EventAttendee.user_id == current_user.id,
                Events.event_date >= first_day,
                Events.event_date <= last_day
            )
        )
        .order_by(Events.event_date, Events.event_time)
    ).all()
    
    # Create a dictionary of events by date for easy lookup
    events_by_date = {}
    for event in user_events:
        event_date = event.event_date
        if event_date not in events_by_date:
            events_by_date[event_date] = []
        events_by_date[event_date].append(event)
    
    # Create a list of all dates in the month for template iteration
    month_dates = []
    for day in range(1, last_day.day + 1):
        month_dates.append(date(year, month, day))
    
    # Calculate calendar grid
    # Get the first day of the week for the first day of the month
    first_weekday = first_day.weekday()  # Monday is 0, Sunday is 6
    # Adjust for Sunday start (if you want Sunday to be the first day)
    # first_weekday = (first_weekday + 1) % 7
    
    # Calculate previous and next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    form = UpdateUserForm()
    if form.validate_on_submit():

        if form.picture.data:
            # Store the uploaded image temporarily and redirect to crop page
            from werkzeug.utils import secure_filename
            import uuid
            
            filename = secure_filename(form.picture.data.filename)
            temp_filename = str(uuid.uuid4()) + '_' + filename
            temp_path = os.path.join(current_app.root_path, 'static', 'temp', temp_filename)
            
            # Create temp directory if it doesn't exist
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            form.picture.data.save(temp_path)
            
            # Store temp filename in session for cropping
            session['temp_image'] = temp_filename
            
            return redirect(url_for('users.crop_image'))
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('users.account'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('account.html', 
                         form=form, 
                         events_by_date=events_by_date,
                         month=month,
                         year=year,
                         first_day=first_day,
                         last_day=last_day,
                         first_weekday=first_weekday,
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year,
                         month_name=calendar.month_name[month],
                         today=date.today(),
                         month_dates=month_dates)

@users.route('/crop_image', methods = ['GET', 'POST'])
@login_required
def crop_image():
    if 'temp_image' not in session:
        flash('No image to crop', 'error')
        return redirect(url_for('users.account'))
    
    temp_filename = session['temp_image']
    temp_path = os.path.join(current_app.root_path, 'static', 'temp', temp_filename)
    
    if not os.path.exists(temp_path):
        flash('Temporary image not found', 'error')
        return redirect(url_for('users.account'))
    
    if request.method == 'POST':
        # Get crop data from form
        crop_x = int(request.form.get('crop_x', 0))
        crop_y = int(request.form.get('crop_y', 0))
        crop_width = int(request.form.get('crop_width', 100))
        crop_height = int(request.form.get('crop_height', 100))
        
        crop_data = (crop_x, crop_y, crop_width, crop_height)
        
        # Process the image with cropping
        username = current_user.username
        pic = add_profile_pic(temp_path, username, crop_data)
        current_user.profile_image = pic
        
        current_user.username = request.form.get('username', current_user.username)
        current_user.email = request.form.get('email', current_user.email)
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(temp_path)
        session.pop('temp_image', None)
        
        flash('Your profile picture has been updated!', 'success')
        return redirect(url_for('users.account'))
    
    # Show crop interface
    image_url = url_for('static', filename='temp/' + temp_filename)
    return render_template('crop_image.html', image_url=image_url)

@users.route('/<username>')
def user_events(username):
    page = request.args.get('page', 1, type = int)
    stmt = select(User).where(User.username == username)
    user = db.session.scalar(stmt)

    if user is None:
        abort(404)

    events = db.paginate(
        select(Events).where(Events.author == user).order_by(desc(Events.created_date)),
        page=page,
        per_page=5,
        error_out=False
    )

    return render_template('user_events.html', events = events, user = user)