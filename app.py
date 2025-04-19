'''back-end'''
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from collections import defaultdict
from flask import jsonify
# from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.secret_key = "very_secure123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Olalaiamfine5162@localhost:5432/base'
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
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)
# треба прописати помилку, якщо не має акаунту
@app.route('/auth/google')
def google_auth():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        print("Помилка", e)
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
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    number = db.Column(db.Text, unique=True)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    bio = db.Column(db.Text)
    verified = db.Column(db.Boolean)

    answers = db.relationship('Answer', back_populates='user', lazy=True)
    answered = db.Column(db.Boolean)
    rating = db.Column(db.Float)
#ДО ЦЬОГО МОМЕНТУ

    reviews_count = db.Column(db.Integer, default=0)

    # зв'язок з рейтингами
    given_ratings = db.relationship("Rating", foreign_keys='Rating.rater_id', backref="rater", lazy=True)
    received_ratings = db.relationship("Rating", foreign_keys='Rating.rated_id', backref="rated", lazy=True)

    events = db.relationship('Events', back_populates='user', lazy=True)
    def __init__(self, occupation, username, email, number, name, \
surname, bio, password, verified=True, rating=None, answered=False):
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

        self.answered = answered


class Events(db.Model):
    '''Events table'''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    accepted = db.Column(db.Boolean)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # needed for the algorithm 
    reviews_count = db.Column(db.Integer, default=0) 

    user = db.relationship('Users', back_populates='events')

    def __init__(self, title, description, date, time, user_id, accepted=False):
        '''for positional arguments'''
        self.title = title
        self.description = description

        self.date = date
        self.time = time

        self.user_id = user_id
        self.accepted = accepted

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_number = db.Column(db.Integer)
    answer_text = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', back_populates='answers')
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
    occupation = user.occupation
    top = top_psychologists()
    return render_template("main.html", occupation=occupation, top=top)

@app.route("/calendar")
def calendar():
    '''calendar page'''
    events = display_events()
    user = Users.query.filter_by(username=session['user']).first()
    occupation = user.occupation
    return render_template("calendar.html", occupation=occupation, events=events)

@app.route('/profile/<username>', methods=["GET", "POST"])
def profile(username):
    profile_user = Users.query.filter_by(username=username).first()
    current_user = Users.query.filter_by(username=session["user"]).first()

    if not profile_user:
        return render_template("error.html", error_message="No user with this username")

    if request.method == "POST" and current_user.occupation == "military" and profile_user.occupation == "psychologist":
        score = float(request.form["rating"])
        existing = Rating.query.filter_by(rater_id=current_user.id, rated_id=profile_user.id).first()

        if existing:
            existing.score = score
        else:
            rating = Rating(rater_id=current_user.id, rated_id=profile_user.id, score=score)
            db.session.add(rating)
            current_user.reviews_count += 1

        db.session.commit()
        return redirect(url_for("profile", username=username))

    return render_template('profile.html', user=profile_user, current_user=current_user)

@app.route("/settings")
def settings():
    '''settings page'''
    message = request.args.get('message')
    return render_template("settings.html", message=message)


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

def validate_name(name):
    ''' complitad regex for username min. 3 char and max. 30, special
    characters can be allowed, if all characters are only special 
    characters it should return false'''
    if not name:
        return None
    regex = "^[A-Za-z0-9]{1,30}$"
    return re.fullmatch(regex, name) is not None

def validate_email(email):
    '''regex for email'''
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.fullmatch(regex, email) is not None

def validate_password_1(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^.{8,20}$"
    return re.fullmatch(regex, password) is not None
def validate_password_2(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^(?=.*\d).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_3(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^(?=.*[A-Z]).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_4(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = r"^[a-zA-Z0-9]+$"
    return re.fullmatch(regex, password) is not None
def validate_number(number):
    '''must be checked '''
    regex = r"^\+?[0-9]{10,15}$"
    return re.fullmatch(regex, number) is not None

@app.route("/save", methods=["POST"])
def save_user():
    '''saves user to file'''
    occupation = request.form["occupation"]
    match occupation:
        case 'military':
            page = "m-register.html"
        case "psychologist":
            page = "ps-register.html"
        case "volunteer":
            page = "v-register.html"
    username = request.form["username"]

    if not validate_name(username):
        return render_template(page, error_message="Invalid username")

    email = request.form["email"]

    if not validate_email(email):
        return render_template(page, error_message="Invalid email format")

    password = request.form["password"]
    if not validate_password_1(password):
        return render_template(page, error_message="Invalid password format: Minimum 8 and maximum 20 characters")
    if not validate_password_2(password):
        return render_template(page, error_message="Invalid password format: Minimum 1 digit")
    if not validate_password_3(password):
        return render_template(page, error_message="Invalid password format: Minimum 1 Big letter")
    if not validate_password_4(password):
        return render_template(page, error_message="Invalid password format: Minimum 1 small letter")

    name = request.form.get("name")
    if name:
        if not re.fullmatch(r'^[А-ЩЬЮЯЄІЇа-щьюяєіїA-Za-z]{1,30}$', name):
                return render_template(page, error_message="Invalid name must be between 1-30")
    surname = request.form.get("surname")
    if surname:
        if not re.fullmatch(r'^[А-ЩЬЮЯЄІЇа-щьюяєіїA-Za-z]{1,30}$', surname):
            return render_template(page, error_message="Invalid surname must be between 1- 30")

    bio = request.form.get("bio")
    if bio:
        if not re.fullmatch(r'^.{1,500}$', bio):
            if occupation != 'military':
                return render_template(page, error_message="Invalid bio must be between 1 - 300 symbols")
    number = re.sub(r"[^0-9]", "", request.form.get("number"))\
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

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rated_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    score = db.Column(db.Float, nullable=False)

def calculate_influence_scores():
    ratings = Rating.query.all()
    user_influence = defaultdict(int)

    for r in ratings:
        user_influence[r.user_id] += 1

    return user_influence

def calculate_psychologist_reputation():
    ratings = Rating.query.all()
    scores = defaultdict(lambda: [0, 0])  # rated_id: [total_weighted, total_weight]

    for r in ratings:
        weight = r.rater.reviews_count or 1
        scores[r.rated_id][0] += r.score * weight
        scores[r.rated_id][1] += weight

    reputations = {}
    for pid, (total, weight) in scores.items():
        reputations[pid] = round(total / weight, 2) if weight > 0 else 0.0

    return reputations
def update_user_rating(user_id):
    '''оновлює рейтинг психолога в Users після оцінки'''
    rep_scores = calculate_psychologist_reputation()
    user = Users.query.get(user_id)
    if user:
        user.rating = rep_scores.get(user.id, 0.0)
        db.session.commit()
@app.route("/psychologists")
def psychologist_list():
    current_user = Users.query.filter_by(username=session["user"]).first()

    if current_user.occupation != "military":
        return render_template("error.html", error_message="Лише для військових")

    # if not current_user.questionnaire:
    #     return redirect(url_for("questions"))
    rep_scores = calculate_psychologist_reputation()
    psychologists = Users.query.filter_by(occupation="psychologist").all()

    # psychologists = [p for p in psychologists if p.questionnaire]
    # psychologists = [p for p in psychologists]
    for p in psychologists:
        p.rating = rep_scores.get(p.id, 0.0)

    psychologists_sorted = sorted(psychologists, key=lambda p: p.rating, reverse=True)
    return render_template("psychologists.html", psychologists=psychologists_sorted)

@app.route("/questionnaire", methods=["GET", "POST"])
def questions():
    user = Users.query.filter_by(username=session['user']).first()
    return render_template("questions.html", user=user)

@app.route('/submit-questionnaire', methods=['POST'])
def submit_questionnaire():
    user = Users.query.filter_by(username=session['user']).first()
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"status": "error", "message": "Немає даних"}), 400

    user_id = user.id
    answers = data.get('answers')
    print(user_id)
    if not user_id or not answers:
        return jsonify({"status": "error", "message": "Неправильні дані"}), 400

    if not user:
        return jsonify({"status": "error", "message": "Користувача не знайдено"}), 404

    for idx, (question_key, response) in enumerate(answers.items(), start=1):
        existing_answer = Answer.query.filter_by(user_id=user_id, question_number=idx).first()

        if existing_answer:
            existing_answer.answer_text = response
        else:
            new_answer = Answer(
                question_number=idx,
                answer_text=response,
                user_id=user_id
            )
            db.session.add(new_answer)

    user.answered = True
    db.session.commit()

    return jsonify({"status": "ok"})
@app.route("/psychologist/<username>", methods=["GET", "POST"])
def view_psychologist(username):
    profile_user = Users.query.filter_by(username=username).first()  # психолог
    current_user = Users.query.filter_by(username=session['user']).first()  # військовий

    if request.method == "POST" and current_user.occupation == "military" and profile_user.occupation == "psychologist":
        score = float(request.form["rating"])

        existing = Rating.query.filter_by(rater_id=current_user.id, rated_id=profile_user.id).first()
        if existing:
            existing.score = score
        else:
            new_rating = Rating(rater_id=current_user.id, rated_id=profile_user.id, score=score)
            db.session.add(new_rating)
            current_user.reviews_count = (current_user.reviews_count or 0) + 1

        db.session.commit()
        update_user_rating(profile_user.id)

        return redirect(url_for("profile", username=username))

    return render_template("profile.html", user=profile_user, current_user=current_user)


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

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
