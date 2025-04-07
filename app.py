'''back-end'''
import re
from flask import Flask, render_template, request, redirect, url_for, session #Response
from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.secret_key = "very_secure123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:very_secure321@localhost:5432/base'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



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

    picture = db.Column(db.LargeBinary)
    rating = db.Column(db.Float)

    events = db.relationship('Events', backref='users', lazy=True)

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
    '''Events table'''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    accepted = db.Column(db.Boolean)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image = db.relationship('Images', backref='events', uselist=False, cascade='all, delete')

    def __init__(self, title, description, date, time, user_id, accepted=False):
        '''for positional arguments'''
        self.title = title
        self.description = description

        self.date = date
        self.time = time

        self.user_id = user_id
        self.accepted = accepted

class Images(db.Model):
    '''Images table'''
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(50), nullable=False)

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), unique=True, nullable=False)

    def __init__(self, filename, data, mimetype, event_id):
        '''for positional arguments'''
        self.filename = filename
        self.data = data
        self.mimetype = mimetype
        self.event_id = event_id

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
    error_message = request.args.get('error_message')
    return render_template("m-register.html", error_message=error_message)

@app.route('/sign-in-psychologist')
def ps_register():
    '''sign up page'''
    error_message = request.args.get('error_message')
    return render_template("ps-register.html", error_message=error_message)

@app.route('/sign-in-volunteer')
def v_register():
    '''sign up page'''
    error_message = request.args.get('error_message')
    return render_template('v-register.html', error_message=error_message)

@app.route("/login")
def login():
    '''sign up page'''
    error_message = request.args.get('error_message')
    return render_template("login.html", error_message=error_message)

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
        return redirect(url_for("login", error_message="No account with this username"))

    if user.password == password:
        if user.verified or user.occupation != "psychologist":
            session["user"] = username
            return redirect(url_for("main"))

        return redirect(url_for("login", error_message="Wait for the verification"))

    return redirect(url_for("login", error_message="Wrong password"))

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

    match occupation:
        case 'military':
            user = Users(occupation, username, email, number, name, surname, bio, password, True)
            page = "m_register"
        case "psychologist":
            user = Users(occupation, username, email, number, name, surname, bio,password,False,0.0)
            page = "ps_register"
        case "volunteer":
            user = Users(occupation, username, email, number, name, surname, bio, password, False)
            page = "v_register"

    if not used(username):
        if occupation == "psychologist":
            return redirect(url_for(""))
        add_to_db(user)
        session["user"] = username
        return redirect(url_for("main"))

    return redirect(url_for(page, error_message="Account with this username already exists"))

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
    psychologists = Users.query.filter_by(occupation="psychologist", verified=True).all()
    if psychologists:
        return sorted(sorted(psychologists, key=lambda p: p.username),\
key=lambda p: p.rating, reverse=True)[:3]

@app.route("/thank-you-for-registration")
def waiting():
    '''waiting page'''
    return render_template("waiting-page.html")

@app.route("/add-event")
def add_event_page():
    '''add event page'''
    message = request.args.get('message')
    return render_template("add-event.html", message=message)

@app.route("/save-event", methods=["POST"])
def add_event():
    '''saving event'''
    name = request.form["name"]
    description = request.form["description"]
    date = request.form["date"]
    time = request.form["time"]

    picture = request.files["picture"]

    user = Users.query.filter_by(username=session["user"]).first()
    accepted = user.verified

    event = Events(name, description, date, time, user.id, accepted)
    add_to_db(event)

    if picture:
        image = (name, picture, picture.mimetype)
        add_to_db(image)


    if accepted:
        #renew event
        message = "Подія була додана в календар. Дякую!"

    else:
        message = "Дякую за подію! Після верифікації вона буде додана до календаря подій"

    return redirect(url_for("add_event_page", message=message))

def display_events():
    '''displays events'''
    pass


# def display_image():
#     '''displays image'''
#     days = Events.query.filter_by(verified=True).with_entities(Events.date).all()
#     days = sorted(days, key=lambda d: )
#     if days:

#get picture
#display calendar
#settings
#admin stuff
#questions **

#regex
#oauth


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
