"""
    GitHub Example
    --------------

    Shows how to authorize users with Github.

"""
from flask import Flask, request, g, session, redirect, url_for, render_template
from flask import render_template_string, jsonify
from werkzeug.utils import secure_filename

from flask_github import GitHub
from functools import wraps

from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from dotenv import load_dotenv
import os

import time

DATABASE_URI = "sqlite:///database.db"
SECRET_KEY = 'development key'
DEBUG = True

# Set these values


# get the two values above from an env file
load_dotenv()
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

# setup flask
app = Flask(__name__)
app.config.from_object(__name__)

# setup github-flask
github = GitHub(app)

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(Text, nullable=False)
    github_login = Column(Text, nullable=False)
    github_link = Column(Text, nullable=False)
    github_avatar = Column(Text, nullable=False)

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


# create a new table named problems
class Problems(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    slug = Column(Text, nullable=False)


# create a new class named submissionsbin
class Submissions(Base):
    __tablename__ = 'submissionsbin'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)


# create the table in the database
init_db()


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/')
def index():
    if g.user:
        t = 'Hello! %s <a href="{{ url_for("user") }}">Get user</a> ' \
            '<a href="{{ url_for("repo") }}">Get repo</a> ' \
            '<a href="{{ url_for("logout") }}">Logout</a>'
        t %= g.user.github_login
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template('index.html', g=g)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token

    print(github)

    # Not necessary to get these details here
    # but it helps humans to identify users easily.
    g.user = user
    github_user = github.get('/user')
    user.github_link = github_user['html_url']
    user.github_avatar = github_user['avatar_url']
    user.github_login = github_user['login']

    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize()
    else:
        return 'Already logged in'


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user')
def user():
    return jsonify(github.get('/user'))


@app.route('/repo')
def repo():
    return jsonify(github.get('/repos/cenkalti/github-flask'))


@app.route('/problems')
@login_required
def problems():
    problems = Problems.query.all()
    return render_template('problems.html', problems=problems)


@app.route('/problem')
@login_required
def problem():
    problem = Problems.query.filter_by(id=request.args.get('problem_id')).first()
    if problem is None:
        return 'Problem not found, please try again'  # TODO replace with a 404 page, with redirect to problems page

    # get the first 10 least size submissionsbin for this problem where pass = true
    submissions = Submissions.query.filter_by(problem_id=problem.id, check='pass').order_by(Submissions.size).limit(10).all()

    return render_template('problem.html', problem=problem, submissions=submissions)


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        # get the problem slug from the database
        problem = Problems.query.filter_by(id=request.form.get('problem_id')).first()
        if problem is None:
            return 'Problem not found, please try again'  # TODO replace with a 404 page, with redirect to problems page

        # create a new submission
        submission = Submissions(problem_id=problem.id, user_id=g.user.id, check=check, size=size, time=int(time.time()))

        # add the submission to the database
        db_session.add(submission)
        db_session.commit()

    else:
        return render_template('submit.html', problem=Problems.query.filter_by(id=request.args.get('id')).first())


@app.route('/submissions')
@login_required
def submissions():
    # get the last 20 submissionsbin by the time they were submitted, join the problems table and get the name of the problem, join users table and get the of the user and their github link and there avatar link
    submissions = Submissions.query.order_by(Submissions.id.desc()).join(Problems, Problems.id == Submissions.problem_id).add_columns(Problems.name).join(User, User.id == Submissions.user_id).add_columns(User.github_login, User.github_link, User.github_avatar).limit(20).all()
    print(submissions)
    # get all the submissionsbin that the user has submitted, join the problems table and get the name of the problem
    user_submissions = Submissions.query.filter_by(user_id=session['user_id']).join(Problems, Problems.id == Submissions.problem_id).add_columns(Problems.name).all()

    return render_template('submissions.html', submissions=submissions, user_submissions=user_submissions, convert=time.ctime)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)