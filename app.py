'''back-end'''
import re
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
# from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.secret_key = "very_secure123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:very_secure321@localhost:5432/base'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#oauth
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='200018166534-78genr8bc0as1eq485m832fe76mvor26.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={
        'access_type': 'offline',
        'prompt': 'consent'
    },
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google')
def google_auth():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    email = user_info['email']
    username = user_info.get('name', email.split('@')[0])

    user = Users.query.filter_by(email=email).first()
    if not user:
        return render_template('login.html', error_message="No account with this username")
    session['user'] = user.username
    return redirect(url_for('main'))
#oauth
class Users(db.Model):
    '''Users table'''
    id = db.Column(db.Integer, primary_key=True)
    occupation = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    number = db.Column(db.String(320), unique=True)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    bio = db.Column(db.String(500))
    verified = db.Column(db.Boolean)

    picture = db.Column(db.Text)
    rating = db.Column(db.Float)

    def __init__(self, occupation, username, email, number, name, \
surname, bio, password, verified=True, rating=None):
        '''for positional arguments'''
        self.occupation = occupation
        self.username = username
        self.email = email

        self.number = number
        self.name = name
        self.surname = surname
        self.bio = bio

        self.password = password #add hashing
        self.verified = verified

        self.rating = rating

class Events(db.Model):
    '''Event table'''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    picture = db.Column(db.Text)
    accepted = db.Column(db.Boolean)

    def __init__(self, title, description, picture):
        '''for positional arguments'''
        self.title = title
        self.description = description
        self.picture = picture
        self.accepted = False



@app.before_request
def restricted_pages():
    '''redirects unauthorized users'''
    restricted = ["/main", "/calendar", "/profile", "/settings", "/questionnaire", "/logout"]
    if request.path in restricted and "user" not in session:
        return redirect(url_for("start"))

@app.before_request
def previous_url():
    '''stores visited URL'''
    if request.endpoint not in ["static"]:
        session["prev_url"] = request.referrer



@app.route("/")
@app.route("/start")
def start():
    '''registration page'''
    return render_template('start.html')

@app.route("/logout")
def logout_page():
    '''logout page'''
    return render_template("logout.html")

@app.route("/main")
def main():
    '''main page'''
    user = Users.query.filter_by(username=session['user']).first()
    occupation = user.occupation
    top = top_psychologists()
    return render_template("main.html", occupation=occupation, top=top)

@app.route("/calendar")
def calendar():
    '''calendar page'''
    user = Users.query.filter_by(username=session['user']).first()
    occupation = user.occupation
    return render_template("calendar.html", occupation=occupation)

@app.route("/questionnaire")
def questions():
    '''questionnaire page'''
    return render_template("questions.html")

@app.route("/profile")
def profile():
    '''profile page'''
    return render_template("profile.html")

@app.route("/settings")
def settings():
    '''settings page'''
    return render_template("settings.html")


@app.route("/sign-in-military")
def m_register():
    '''sign up page'''
    return render_template("m-register.html")

@app.route('/sign-in-psychologist')
def ps_register():
    '''sign up page'''
    return render_template("ps-register.html")

@app.route('/sign-in-volunteer')
def v_register():
    '''sign up page'''
    return render_template('v-register.html')

@app.route("/login")
def login():
    '''sign up page'''
    return render_template("login.html")

@app.route("/approving-psychologist")
def ps_approving():
    '''after signing up page'''
    return render_template("ps-approving.html")

@app.route("/approving-event")
def v_approving():
    '''after sending event page'''
    return render_template('v-approving.html')



@app.route("/validation", methods=["POST"])
def validate_user():
    '''validates user'''
    username = request.form["username"]
    password = request.form["password"]

    user = Users.query.filter_by(username=username).first()

    if not user:
        return render_template('login.html', error_message="No account with this username")

    if user.password == password:
        if user.verified:
            session["user"] = username
            return redirect(url_for("main"))

        return render_template("login.html", error_message="Wait for the verification")

    return render_template("login.html", error_message="Wrong password")

@app.route("/save", methods=["POST"])
def save_user():
    '''saves user to file'''
    occupation = request.form["occupation"]

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    name = request.form.get("name")
    surname = request.form.get("surname")
    bio = request.form.get("bio")
    number = re.sub(r"[^0-9]", "", request.form.get("number")) \
if request.form.get("number") else None

    if occupation == 'military':
        user = Users(occupation, username, email, number, name, surname, bio, password, True)

    else:
        user = Users(occupation, username, email, number, name, surname, bio, password, False, 0.0)
    # regex 
    # if 
    if not used(username):
        add_to_db(user)
        session["user"] = username
        return redirect(url_for("main"))
    #regex
    match occupation:
        case 'military':
            page = "m-register.html"
        case "psychologist":
            page = "ps-register.html"
        case "volunteer":
            page = "v-register.html"

    return render_template(page, error_message="Account with this username already exists")

def used(username):
    '''checks if name is already in use'''
    return Users.query.filter_by(username=username).first()

def add_to_db(data):
    '''writes data to the database'''
    db.session.add(data)
    db.session.commit()

@app.route("/complete-logout")
def logout():
    '''logout function'''
    session.pop("user", None)
    session.clear()
    return redirect(url_for("start"))

def create_tables():
    '''creates tables if not created'''
    with app.app_context():
        db.create_all()

def top_psychologists():
    '''sort psycholists by rating'''
    psychologists = Users.query.filter_by(occupation="psychologist").all()
    if psychologists:
        return sorted(sorted(psychologists, key=lambda p: p.username),\
key=lambda p: p.rating, reverse=True)[:3]



if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
