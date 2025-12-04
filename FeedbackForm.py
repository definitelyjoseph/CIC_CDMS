from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField,DateField
from wtforms.validators import DataRequired,Email, Length
from wtforms.fields import DateField

class FeedbackForm(FlaskForm):
    Name = StringField('Name', 
                              validators=[DataRequired(),Length(min=5, max=20)])
    School_name = StringField('School Name', 
                              validators=[DataRequired(),Length(min=10, max=150)])
    Email = EmailField('Email', 
                               validators=[DataRequired(), Email()])
    Feedback = TextAreaField('Feedback',
                             validators=[DataRequired(),Length(min=20, max=1500)])
    TripDate =  DateField('Trip Date',
                          format='%Y-%m-%d',validators=[DataRequired()])
    Submit = SubmitField('Submit Feedback')
    Admin_Login = SubmitField('Admin Login') 
