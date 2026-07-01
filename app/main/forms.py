import os
from flask import Flask, render_template, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_mail import Mail, Message

class ContactForm(FlaskForm):
    """Contact form definition."""
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=1, max=64)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    company = StringField('Company Name', validators=[Optional(), Length(max=100)])
    website = StringField('Website URL', validators=[Optional(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send Message')

