from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Optional

class EventForm(FlaskForm):
    event_title = StringField('Event Title', validators=[DataRequired()])
    event_description = TextAreaField('Event Description', validators=[DataRequired()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    event_time = TimeField('Event Time', validators=[DataRequired()])
    location = StringField('Location (Address)', validators=[DataRequired()])
    purpose = SelectField('What is your purpose for attending?', 
                         choices=[('Buy', 'Buy items'), 
                                 ('Sell', 'Sell items'), 
                                 ('Both', 'Both buy and sell')],
                         validators=[DataRequired()])
    items_bringing = TextAreaField('What items are you planning to bring? (Only fill if you selected "Sell" or "Both")', 
                                  validators=[Optional()])
    submit = SubmitField('Create Event')

class JoinEventForm(FlaskForm):
    attendance_likelihood = SelectField('How likely are you to attend?', 
                                      choices=[('Definitely', 'Definitely'), 
                                              ('Possibly', 'Possibly'), 
                                              ('Maybe', 'Maybe')],
                                      validators=[DataRequired()])
    purpose = SelectField('What is your purpose for attending?', 
                         choices=[('Buy', 'Buy items'), 
                                 ('Sell', 'Sell items'), 
                                 ('Both', 'Both buy and sell')],
                         validators=[DataRequired()])
    items_bringing = TextAreaField('What items are you planning to bring? (Only fill if you selected "Sell" or "Both")', 
                                  validators=[Optional()])
    submit = SubmitField('Join Event')

class EventSearchForm(FlaskForm):
    event_name = StringField('Event Name', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    items_search = StringField('Items Being Brought', validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    submit = SubmitField('Search Events')