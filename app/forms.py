from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class DatabaseCheck(object):
    def __init__(self, db_field, check_exists=False, message=None, lowercase=False):
        self.db_field = db_field
        self.lowercase = lowercase
        self.check_exists = check_exists
        self.field_name = str(db_field).split('.', 1)[1]
        self.message = message
        if not message:
            if self.check_exists:
                self.message = f"No user with this {self.field_name} exists."
            else:
                self.message = f"User with this {self.field_name} already exists."

    def __call__(self, form, field):
        if self.field_name == "password":
            username_input = form["username"].data
            user = User.query().filter(User.username == username_input).first()
            if not user or not user.check_password(field.data):
                raise ValidationError(self.message)

        else:
            if self.lowercase:
                user = User.query().filter(self.db_field == field.data.lower()).first()
            else:
                user = User.query().filter(self.db_field == field.data).first()
            if user and not self.check_exists or \
                    not user and self.check_exists:
                raise ValidationError(self.message)


class LoginForm(FlaskForm):
    """USER LOGIN FORM"""  # TODO: Move checks into here from login route
    username = StringField("Username",
                           validators=[DataRequired(),
                                       Length(max=32, message="Username invalid!")
                                       ])
    password = PasswordField("Password",
                             validators=[DataRequired(),
                                         DatabaseCheck("User.password", message="Username or password invalid!")
                                         ])


class RegisterForm(FlaskForm):
    """USER SIGN UP FORM"""
    username = StringField("Username",
                           validators=[DataRequired(),
                                       Length(max=32, message="Username must be less than 33 characters long"),
                                       DatabaseCheck(User.username, check_exists=False)
                                       ])
    password = PasswordField("Password",
                             validators=[DataRequired(),
                                         Length(min=8, message="Password must be longer than 8 characters")
                                         ])
    confirm = PasswordField("Confirm password",
                            validators=[EqualTo('password', message="Passwords must match"),
                                        DataRequired()
                                        ])
    first_name = StringField("First name",
                             validators=[DataRequired(),
                                         Length(max=32, message="Name should be less than 33 characters long")
                                         ])
    last_name = StringField("Last name",
                            validators=[DataRequired(),
                                        Length(max=32, message="Name should be less than 33 characters long")
                                        ])
    pref_name = StringField("Preferred name",
                            validators=[Length(max=32, message="Name should be less than 33 characters long")
                                        ])
    email = StringField("Email",
                        validators=[DataRequired(),
                                    Email(message="Not a valid email address."),
                                    DatabaseCheck(User.email, check_exists=False, lowercase=True),
                                    ])
    tos = BooleanField('I accept the TOS', [DataRequired()])
