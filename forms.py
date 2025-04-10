from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from datetime import datetime, date

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    birth_date = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_birth_date(self, birth_date):
        if birth_date.data:
            today = date.today()
            age = today.year - birth_date.data.year - ((today.month, today.day) < (birth_date.data.month, birth_date.data.day))
            if age < 13:
                raise ValidationError('Você deve ter pelo menos 13 anos para se cadastrar.')

class ItemForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Descrição', validators=[Length(max=500)])
    submit = SubmitField('Salvar')

class UpdateProfileForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    birth_date = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[])
    submit = SubmitField('Atualizar')

    def validate_birth_date(self, birth_date):
        if birth_date.data:
            today = date.today()
            age = today.year - birth_date.data.year - ((today.month, today.day) < (birth_date.data.month, birth_date.data.day))
            if age < 13:
                raise ValidationError('Você deve ter pelo menos 13 anos.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')

class AdminUserCreateForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    birth_date = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = StringField('Perfil', validators=[DataRequired()])
    submit = SubmitField('Criar Usuário')

class AdminUserEditForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    birth_date = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[])
    role = StringField('Perfil', validators=[DataRequired()])

    # Campos para alterar a senha (opcionais)
    change_password = BooleanField('Alterar Senha')
    password = PasswordField('Nova Senha', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[Optional(), EqualTo('password')])

    submit = SubmitField('Atualizar Usuário')
