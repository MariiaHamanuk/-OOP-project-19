'''back-end'''
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
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
    email = db.Column(db.Text, unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.Text, nullable=False)

    number = db.Column(db.Text, unique=True)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    bio = db.Column(db.Text)
    verified = db.Column(db.Boolean)

    answered = db.Column(db.Boolean)
    rating = db.Column(db.Float)


    events = db.relationship('Events', back_populates='user', lazy=True)
    answer = db.relationship('Answers', back_populates='user', uselist=False)

    def __init__(self, occupation, username, email, number, name, \
surname, bio, password, verified=True, rating=None, age=None):
        '''for positional arguments'''
        self.occupation = occupation
        self.username = username
        self.email = email
        self.age = age

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
    description = db.Column(db.Text, nullable=False)
    accepted = db.Column(db.Boolean)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('Users', back_populates='events')

    def __init__(self, title, description, date, time, user_id, accepted=False):
        '''for positional arguments'''
        self.title = title
        self.description = description

        self.date = date
        self.time = time

        self.user_id = user_id
        self.accepted = accepted

class Answers(db.Model):
    '''Answers table'''
    id = db.Column(db.Integer, primary_key=True)
    online = db.Column(db.Boolean, nullable=False)
    experience = db.Column(db.Boolean, nullable=False)
    activities = db.Column(db.Boolean, nullable=False)
    good_age = db.Column(db.Integer)
    english = db.Column(db.Boolean, nullable=False)

    user = db.relationship('Users', back_populates='answer')

    def __init__(self, online, experience, activities, english, user_id, good_age=None):
        '''for positional arguments'''
        self.online = online
        self.experience = experience
        self.activities = activities
        self.good_age = good_age
        self.english = english

        self.user_id = user_id




@app.before_request
def restricted_pages():
    '''redirects unauthorized users'''
    restricted = ["/main", "/calendar", "/settings", "/questionnaire", "/logout"]
    if (request.path in restricted or re.match(r"^/profile/[^/]+$", request.path)) \
       and "user" not in session:
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
    top = top_psychologists()[:5]
    return render_template("main.html", occupation=user.occupation, top=top, user=user)

@app.route("/calendar")
def calendar():
    '''calendar page'''
    events = display_events()
    user = Users.query.filter_by(username=session['user']).first()
    occupation = user.occupation
    return render_template("calendar.html", occupation=occupation, events=events)

@app.route("/questionnaire")
def questions():
    '''questionnaire page'''
    return render_template("questions.html")

@app.route('/profile/<username>')
def profile(username):
    '''profile page'''
    user = Users.query.filter_by(username=username).first()
    if not user:
        render_template("error.html", error_message="No user with this username")
    return render_template('profile.html', user=user)

@app.route("/settings")
def settings():
    '''settings page'''
    message = request.args.get('message')
    user = Users.query.filter_by(username=session['user']).first()
    return render_template("settings.html", message=message, user=user)


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

@app.route("/waiting")
def waiting_page():
    '''after signing up page'''
    return render_template("waiting-page.html")



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
        add_to_db(user)
        if occupation == "psychologist":
            return redirect(url_for("waiting_page"))
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
key=lambda p: p.rating, reverse=True)

@app.route("/thank-you-for-registration")
def waiting():
    '''waiting page'''
    return render_template("waiting-page.html")

@app.route("/add-event")
def add_event_page():
    '''add event page'''
    message = request.args.get('message')
    auto_verify()
    events_autodeletion()
    return render_template("add-event.html", message=message)

@app.route("/save-event", methods=["POST"])
def add_event():
    '''saving event'''
    name = request.form["name"]
    description = request.form["description"]
    date = request.form["date"]
    time = request.form["time"]

    year, month, day = list(map(int, date.split("-")))
    hour, minute = list(map(int, time.split(":")))

    user = Users.query.filter_by(username=session["user"]).first()
    accepted = user.verified

    if datetime(year, month, day, hour, minute) >= datetime.now():
        event = Events(name, description, date, time, user.id, accepted)
        add_to_db(event)

        if accepted:
            message = "Подія була додана в календар. Дякую!"

        else:
            message = "Дякую за подію! Після верифікації вона буде додана до календаря подій"
    else:
        message = "Неправильна дата"

    return redirect(url_for("add_event_page", message=message))

def display_events():
    '''displays events'''
    events = Events.query.filter_by(accepted=True).all()

    if events:
        events = sorted(events, key=lambda e: float(e.time.replace(":", '.'))) #by time
        events = sorted(events, key=lambda e: int(e.date.split("-")[0])) #by day
        events = sorted(events, key=lambda e: int(e.date.split("-")[1])) #by month
        events = sorted(events, key=lambda e: int(e.date.split("-")[2])) #by year

    return events

@app.route("/save-answer", methods=["POST"])
def save_answer():
    '''saves answer'''

@app.route("/verify")
def verify_page():
    '''manual verification of users and events'''
    message = request.args.get('message')
    return render_template("verify.html", message=message)


@app.route("/verify-manual",  methods=["POST"])
def verify_manual():
    '''manual user/event verifier'''
    username = request.form.get("user")
    eventname = request.form.get("event")

    message = ""

    if username:
        user = Users.query.filter_by(username=username).first()
        if user:
            user.verified = not user.verified
            db.session.commit()
            message = f"{user.username} {"un" if not user.verified else ""}verified"
        else:
            message = "Invalid username"

    if eventname:
        event = Users.query.filter_by(title=eventname).first()
        if event:
            event.accepted = not event.accepted
            db.session.commit()
            message = f"{event.title} {"un" if not event.accepted else ""}accepted"
        else:
            message = "Invalid event name"
    return redirect(url_for('verify_page', message=message))

def events_autodeletion():
    '''deletes expired events'''
    events = Events.query.all()
    for event in events:
        year, month, day = list(map(int, event.date.split("-")))
        if datetime(year, month, day).date() < datetime.now().date():
            db.session.delete(event)
            db.session.commit()

def auto_verify():
    '''auto verification'''
    user = Users.query.filter_by(username=session["user"]).first()

    if sum(1 for event in user.events if event.accepted):
        user.verified = True

@app.route("/update-info", methods=["POST"])
def update_info():
    '''updates info about user'''
    user = Users.query.filter_by(username = session['user']).first()

    username = request.form.get("username")
    bio = request.form.get("bio")
    email = request.form.get("email")
    number = request.form.get("number")
    new_password = request.form.get("new_password")

    message = "Неправильний пароль"

    if user.password == request.form["password"]:
        user.username = username if username else user.username
        user.bio = bio if bio else user.bio
        user.email = email if email else user.email
        user.number = number if number else user.number
        user.password = new_password if new_password else user.password
        db.session.commit()

        session["user"] = user.username
        message = "Дані успішно оновлено"

    return redirect(url_for('settings', message=message))


@app.route("/account-deletion", methods=["POST"])
def delete_account():
    '''deletes account completely'''
    user = Users.query.filter_by(username=session["user"]).first()
    if user.password == request.form["password"]:
        Events.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        logout()

    return redirect(url_for('settings', message="Неправильний пароль"))

#decomposition

#email mailing
#hashing passwords


#questions
#rating system

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
