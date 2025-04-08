from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from .models import User, Item, db
from .forms import LoginForm, RegistrationForm, ItemForm

routes = Blueprint('routes', __name__)

@routes.route('/')
@routes.route('/index')
def index():
    return render_template('index.html', title='Home')

@routes.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html', title='Register', form=form)

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@routes.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@routes.route('/dashboard')
@login_required
def dashboard():
    items = Item.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', items=items)

@routes.route('/item/new', methods=['GET', 'POST'])
@login_required
def new_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(title=form.title.data, description=form.description.data, owner=current_user)
        db.session.add(item)
        db.session.commit()
        flash('Your item has been created!', 'success')
        return redirect(url_for('routes.dashboard'))
    return render_template('create_item.html', title='New Item', form=form)

@routes.route('/item/<int:item_id>')
@login_required
def item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to view this item.', 'danger')
        return redirect(url_for('routes.dashboard'))
    return render_template('item.html', title=item.title, item=item)

@routes.route('/item/<int:item_id>/update', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to update this item.', 'danger')
        return redirect(url_for('routes.dashboard'))
    form = ItemForm()
    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        db.session.commit()
        flash('Your item has been updated!', 'success')
        return redirect(url_for('routes.item', item_id=item.id))
    elif request.method == 'GET':
        form.title.data = item.title
        form.description.data = item.description
    return render_template('create_item.html', title='Update Item', form=form)

@routes.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(url_for('routes.dashboard'))
    db.session.delete(item)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('routes.dashboard'))
