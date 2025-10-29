from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from sqlalchemy import select

from the_greenhouse import db
from flask_login import current_user
from the_greenhouse.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_pass = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match!')])
    submit = SubmitField('Sign Up Now!')

    def validate_email(self, field):
        user = db.session.execute(
            select(User).filter_by(email=field.data)
        ).scalar_one_or_none()
        if user:
            raise ValidationError("This email is already registered.")

    def validate_username(self, field):
        user = db.session.execute(
            select(User).filter_by(username=field.data)
        ).scalar_one_or_none()
        if user:
            raise ValidationError("This username is already taken.")
        
class UpdateUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    submit = SubmitField('Save Changes')

    def validate_email(self, field):
        user = db.session.execute(
            select(User).filter_by(email=field.data)
        ).scalar_one_or_none()
        if user and user != current_user:
            raise ValidationError("This email is already registered.")

    def validate_username(self, field):
        user = db.session.execute(
            select(User).filter_by(username=field.data)
        ).scalar_one_or_none()
        if user and user != current_user:
            raise ValidationError("This username is already taken.")