from the_greenhouse import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

class User(db.Model, UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    profile_image = db.Column(db.String(128), nullable = False, default = 'default_profile.png')
    email = db.Column(db.String(64), unique = True, index = True)
    username = db.Column(db.String(64), unique = True, index = True)
    password_hash = db.Column(db.String(256))

    events = db.relationship('Events', backref = 'author', lazy = 'select')
    event_attendances = db.relationship('EventAttendee', backref = 'user', lazy = 'select')

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        print(generate_password_hash(password))
        print(self.password_hash)
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"Username: {self.username}"

class Events(db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    created_date = db.Column(db.DateTime, nullable = False, default = lambda: datetime.now(timezone.utc))
    event_title = db.Column(db.String(140), nullable = False)
    event_description = db.Column(db.Text, nullable = False)
    event_date = db.Column(db.Date, nullable = False)
    event_time = db.Column(db.Time, nullable = False)
    location = db.Column(db.String(200), nullable = False)

    def __init__(self, event_title, event_description, event_date, event_time, location, user_id):
        self.event_title = event_title
        self.event_description = event_description
        self.event_date = event_date
        self.event_time = event_time
        self.location = location
        self.user_id = user_id

    attendees = db.relationship('EventAttendee', backref = 'event', lazy = 'select', cascade = 'all, delete-orphan')
    event_items = db.relationship('EventItem', backref = 'event', lazy = 'select', cascade = 'all, delete-orphan')

    def __repr__(self):
        return f"Event ID: {self.id} -- Created: {self.created_date} -- Title: {self.event_title} -- Date: {self.event_date}"

class EventAttendee(db.Model):
    
    __tablename__ = 'event_attendees'
    
    id = db.Column(db.Integer, primary_key = True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    attendance_likelihood = db.Column(db.String(20), nullable = False)  # 'Definitely', 'Possibly', 'Maybe'
    purpose = db.Column(db.String(20), nullable = False)  # 'Buy', 'Sell', 'Both'
    items_bringing = db.Column(db.Text, nullable = True)  # JSON string of items
    joined_date = db.Column(db.DateTime, nullable = False, default = lambda: datetime.now(timezone.utc))
    
    def __init__(self, event_id, user_id, attendance_likelihood, purpose, items_bringing=None):
        self.event_id = event_id
        self.user_id = user_id
        self.attendance_likelihood = attendance_likelihood
        self.purpose = purpose
        self.items_bringing = items_bringing
    
    def __repr__(self):
        return f"EventAttendee: User {self.user_id} attending Event {self.event_id} - {self.attendance_likelihood}"

class EventItem(db.Model):
    
    __tablename__ = 'event_items'
    
    id = db.Column(db.Integer, primary_key = True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    item_name = db.Column(db.String(200), nullable = False)
    added_date = db.Column(db.DateTime, nullable = False, default = lambda: datetime.now(timezone.utc))
    
    # Add relationship to User
    user = db.relationship('User', backref='event_items', lazy='select')
    
    def __init__(self, event_id, user_id, item_name):
        self.event_id = event_id
        self.user_id = user_id  # This is the user who is bringing the item
        self.item_name = item_name
    
    def __repr__(self):
        return f"EventItem: {self.item_name} by User {self.user_id} for Event {self.event_id}"