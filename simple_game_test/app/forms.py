from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField, TextAreaField, IntegerField
from wtforms import (SubmitField, SelectMultipleField, widgets)
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp, StopValidation, InputRequired
from app.models import User

def get_ethnicities():
    return [(0, "White"), 
            (1, "Black or African American"), 
            (2, "American Indian or Alaska Native"), 
            (3, "Asian"), 
            (4, "Native Hawaiian or Pacific Islander"), 
            (5, "Other")]


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(html_tag='ol', prefix_label=False)
    option_widget = widgets.CheckboxInput()

class MultiCheckboxAtLeastOne():
    def __init__(self, message=None):
        if not message:
            message = 'At least one option must be selected.'
        self.message = message

    def __call__(self, form, field):
        if len(field.data) == 0:
            raise StopValidation(self.message)

class LoginForm(FlaskForm):
    username = StringField("Username (Prolific ID)", validators=[DataRequired()])
    # password = PasswordField("Password", validators=[DataRequired()])
    # remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField("Username (Prolific ID)", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password",
                              validators=[DataRequired(),
                                          EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")


class TrialForm(FlaskForm):
    chosen_bin = StringField()
    feedback_chosen = StringField()
    def validate_chosen_bin(self, chosen_bin):
        if len(chosen_bin.data) < 3:
            raise ValidationError("Please choose a bin")
        if not (chosen_bin.data[0] == "b"):
            raise ValidationError("Please choose a bin")
    switches = StringField()
    submit_trial = SubmitField("Next Trial")

class AttentionCheckForm(FlaskForm):
    prev_rule = RadioField("", choices=[(0, "Rule #1"), (1, "Rule #2"), (2, "Rule #3"), (3, "Rule #4")])
    submit_check = SubmitField("Continue")

class FinalForm(FlaskForm):
    gender = RadioField("", choices=[(0, "Man"), (1, "Woman"), (2, "Non-binary"), (3, "Prefer Not to Respond")])
    ethnicity = MultiCheckboxField("",
                               coerce=int,
                               choices=get_ethnicities(),
                               validators=[MultiCheckboxAtLeastOne()])
    education = RadioField("", choices=[(0, "Less than high school degree"),
                                        (1, "High school graduate (high school diploma or equivalent including GED)"),
                                        (2, "Some college but no degree"), (3, "Associate degree in college (2-year)"),
                                        (4, "Bachelor’s degree in college (4-year)"), (5, "Master’s degree"),
                                        (6, "Doctoral degree"), (7, "Professional degree (JD, MD)")])
    opt_text = TextAreaField()
    age = IntegerField(InputRequired)
    submit_final = SubmitField("Continue")

class ConsentForm(FlaskForm):
    age = RadioField("", choices=[(0, "18-24"), (1, "25-34"), (2, "35-44"), (3, "45-54"), (4, "55-64"), (5, "65-74"), (6, "75-84"), (7, "85 or older")])
    gender =  RadioField("", choices=[(0, "Male"), (1, "Female"), (2, "Non-binary"), ])
    education = RadioField("", choices=[(0, "Less than high school degree"), (1, "High school graduate (high school diploma or equivalent including GED)"), (2, "Some college but no degree"), (3, "Associate degree in college (2-year)"), (4, "Bachelor’s degree in college (4-year)"), (5, "Master’s degree"), (5, "Doctoral degree"), (5, "Professional degree (JD, MD)")])
    ethnicity = RadioField("", choices=[(0, "White"), (1, "Black or African American"), (2, "American Indian or Alaska Native"), (3, "Asian"), (4, "Native Hawaiian or Pacific Islander"), (5, "Other")])
    robot = RadioField("", choices=[(0, "Not at all"), (1, "Slightly"), (2, "Moderately"), (3, "Very"), (4, "Extremely")])
    submit_consent = SubmitField("Ready to begin!")

class TrainingForm(FlaskForm):
    #fail_training = SubmitField("You did not complete the required training, proceed to logout")
    submit_training = SubmitField("Training completed! Click to begin the study.")

class DemoForm(FlaskForm):
    submit_demo = SubmitField("Next Card")

class NoFeedbackSurveyForm(FlaskForm):
    frustration = RadioField("", choices=[(0, "Extremely Frustrating"), (1, "Somewhat Frustrating"), (2, "Neither Frustrating nor Pleasant"), (3, "Somewhat Pleasant"), (4, "Extremely Pleasant")])
    ease_of_teaching = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    opt_text = TextAreaField()
    submit_survey = SubmitField("Submit")

class FeedbackSurveyForm(FlaskForm):
    frustration = RadioField("", choices=[(0, "Extremely Frustrating"), (1, "Somewhat Frustrating"), (2, "Neither Frustrating nor Pleasant"), (3, "Somewhat Pleasant"), (4, "Extremely Pleasant")])
    utility_of_feedback = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    ease_of_teaching = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    # engagement = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    # difficulty = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    # user_learning = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])

    # animacy1 = RadioField("", choices=[(0, "Stagnant"), (1, "Somewhat Stagnant"), (2, "Neutral"), (3, "Somewhat Lively"), (4, "Lively")])
    # animacy2 = RadioField("", choices=[(0, "Inert"), (1, "Somewhat Inert"), (2, "Neutral"), (3, "Somewhat Interactive"), (4, "Interactive")])
    # animacy3 = RadioField("", choices=[(0, "Apathetic"), (1, "Somewhat Apathetic"), (2, "Neutral"), (3, "Somewhat Responsive"), (4, "Responsive")])

    # intelligence1 = RadioField("", choices=[(0, "Incompetent"), (1, "Somewhat Incompetent"), (2, "Neutral"), (3, "Somewhat Competent"), (4, "Competent")])
    # intelligence2 = RadioField("", choices=[(0, "Unintelligent"), (1, "Somewhat Unintelligent"), (2, "Neutral"), (3, "Somewhat Intelligent"), (4, "Intelligent")])

    opt_text = TextAreaField()

    submit_survey = SubmitField("Submit")

class InformativenessForm(FlaskForm):
    informativeness = RadioField("", choices=[(0, "Strongly Disagree"), (1, "Disagree"), (2, "Neutral"), (3, "Agree"), (4, "Strongly Agree")])
    submit_survey = SubmitField("Submit")
   
