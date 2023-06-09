from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required,logout_user, current_user
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
Bootstrap(app)
db = SQLAlchemy(app)

#init login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'






#class for table in database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

#creates a connection between the login and the data in the database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#init forms
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=88)])
    remember = BooleanField('remember me')


##RegistrationForm
class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'


    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    #init the form
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
    
    
    
    
    
    
    
    
    
    
    
 import cx_Oracle
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def query_data(username, password, host, port, service_name, sql):
    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
    conn = cx_Oracle.connect(username, password, dsn=dsn)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

def read_data_from_oracle(instances, sqls, num_threads):
    results = {}
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for instance in instances:
            username = instance['username']
            password = instance['password']
            host = instance['host']
            port = instance['port']
            service_name = instance['service_name']
            for sql in sqls:
                futures.append(executor.submit(query_data, username, password, host, port, service_name, sql))
        for future in as_completed(futures):
            df = future.result()
            results[(df.iloc[0]['INSTANCE_NAME'], df.iloc[0]['SQL_ID'])] = df
    return pd.concat(results.values(), ignore_index=True)
