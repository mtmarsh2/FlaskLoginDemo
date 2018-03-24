from flask import Flask, render_template, request, redirect, url_for, abort, session, Response, jsonify
from flask.ext.login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, \
    check_password_hash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from flask_login import login_user, login_required, current_user, logout_user, LoginManager
from sqlalchemy import func
from flask_login import UserMixin
from models import Account, Accountdata, Base
import yaml
import json
import sys
import time

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = cfg['SQLALCHEMY_DATABASE_URI']

db = SQLAlchemy(app)
app.config["db"] = db
app.config["SECRET_KEY"] = "codechallenge"

login_manager = LoginManager()
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(account_name):
    return db.session.query(Account).filter_by(account_name=account_name).first()


login_manager.init_app(app)


@app.route('/get/<key>')
def get(key):
    account_data = db.session.query(Accountdata).filter_by(key=key).first()
    if not account_data:
        return jsonify({"status": "error", "message": "Key does not exist"}), 400
    if account_data.account_name != current_user.account_name:
        return jsonify({"status": "error", "message": "Key does not belong to current user"}), 400
    return jsonify({"status": "success", "value": account_data.value}), 200


@app.route('/set/<key>', methods=['POST'])
def set(key):
    value = request.form['value']
    account_data = db.session.query(Accountdata).filter_by(key=key).first()
    if account_data and account_data.account_name != current_user.account_name:
        return jsonify({"status": "error", "message": "Key does not belong to current user"}), 400
    if not account_data:
        account_data = Accountdata(key=key, value=value)
    else:
        account_data.value = value
    db.session.add(account_data)
    db.session.commit()
    return jsonify({"status": "success", "value": account_data.value}), 200


@app.route('/')
def home():
    if not current_user.get_id():
        return redirect(url_for('login'))
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'GET':
        if current_user.get_id():
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    if 'account_name' not in request.form.keys() or 'password' not in request.form.keys():
        errors.append("Please enter both a username and password")
    else:
        username = request.form['account_name']
        password = request.form['password']
        registered_user = db.session.query(Account).filter_by(
            account_name=request.form['account_name']).first()
        if not registered_user:
            errors.append("No user found with this account name")
        else:
            if not registered_user.check_password(password):
                errors.append("Account name and password do not match.")
    if errors:
        return jsonify({"status": "error", 'errors': errors}), 400
    login_user(registered_user)
    return redirect(url_for('home'))


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []

    if request.method == 'GET':
        if current_user.get_id():
            return redirect(url_for('home'))
        else:
            return render_template('register.html')
    if db.session.query(Account).filter_by(account_name=request.form['account_name']).count() > 1:
        errors.append('Account name is already taken.')
    if not request.form['account_name']:
        errors.append('Please enter a account name.')
    if not request.form['password']:
        errors.append('Please enter a password.')
    if errors:
        return jsonify({"status": "error", 'errors': errors}), 400

    account = Account(
        account_name=request.form['account_name'],
        active_user=True,
    )
    account.set_password(request.form['password'])
    try:
        db.session.add(account)
        db.session.commit()
    except Exception:
        errors.append("Name is already taken")
    if errors:
        return jsonify({"status": "error", 'errors': errors}), 400

    login_user(account, remember=True)
    success_message = "Your account has been created!"
    return jsonify({"status": "success", "value": success_message}), 200

if __name__ == '__main__':
    if '--recreate_db' in sys.argv:
        Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    app.run()
