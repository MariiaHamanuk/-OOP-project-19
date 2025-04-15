'''back-end'''
import re
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
import json
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

#all of the regex functions
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
    regex = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.fullmatch(regex, email) is not None

def validate_password_1(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = "^.{8,20}$"
    return re.fullmatch(regex, password) is not None
def validate_password_2(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = "^(?=.*\d).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_3(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = "^(?=.*[A-Z]).+$"
    return re.fullmatch(regex, password) is not None
def validate_password_4(password):
    '''Minimum eight and maximum 10 characters, at least one
    uppercase letter, one lowercase letter, one number and one special character:'''
    regex = "^[a-zA-Z0-9]+$"
    return re.fullmatch(regex, password) is not None
def validate_number(number):
    '''must be checked '''
    regex = "^\+?[0-9]{10,15}$"
    return re.fullmatch(regex, number) is not None
#all of the regex functions


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
    #, at least one uppercase letter, one lowercase letter, one number and one special character    if not validate_password(password):
        # return render_template(page, error_message="Invalid password format")

    name = request.form.get("name")
    #single name, WITHOUT spaces, WITH special characters
    if name:
        if not re.fullmatch('^[А-ЩЬЮЯЄІЇа-щьюяєіїA-Za-z]{1, 30}$', name):
            # if occupation != 'military':
                return render_template(page, error_message="Invalid name must be between 1-30")
    # no restriction to the size
    #single name, WITHOUT spaces, WITH special characters
    # no restriction to the size
    surname = request.form.get("surname")
    if surname:
        if not re.fullmatch('^[A-Za-z]$', surname):
            return render_template(page, error_message="Invalid surname must be between 1- 30")

    bio = request.form.get("bio")
    if bio:
        if not re.fullmatch('^.{1,300}$', bio):
            if occupation != 'military':
                return render_template(page, error_message="Invalid bio must be between 1 - 300 symbols")
    number = re.sub(r"[^0-9]", "", request.form.get("number"))\
if request.form.get("number") else None

    if occupation == 'military':
        user = Users(occupation, username, email, number, name, surname, bio, password, True)

    else:
        user = Users(occupation, username, email, number, name, surname, bio, password, False, 0.0)
    # changes    # changes
    if not used(username) and validate_email(email) and validate_name(username) and validate_email(email) and \
validate_password_1(password) and validate_password_2(password) and validate_password_3(password)\
 and validate_password_4(password):
        if not occupation == 'military':
            if validate_number(number) and validate_name(name):
                add_to_db(user)
                session["user"] = username
                return redirect(url_for("main"))
        else:
            add_to_db(user)
            session["user"] = username
            return redirect(url_for("main"))
    return render_template(page, error_message="Account with this username already exists")

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # військовий
    psychologist_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # психолог
    score = db.Column(db.Float, nullable=False)
from collections import defaultdict

def calculate_influence_scores():
    ratings = Rating.query.all()
    user_influence = defaultdict(int)

    for r in ratings:
        user_influence[r.user_id] += 1

    return user_influence

def calculate_psychologist_reputation():
    ratings = Rating.query.all()
    influence = calculate_influence_scores()
    scores = defaultdict(lambda: [0, 0])  # psychologist_id: [total_weighted, total_weight]

    for r in ratings:
        weight = influence[r.user_id]
        scores[r.psychologist_id][0] += r.score * weight
        scores[r.psychologist_id][1] += weight

    reputations = {}
    for pid, (total, weight) in scores.items():
        reputations[pid] = round(total / weight, 2) if weight > 0 else 0.0

    return reputations
@app.route("/psychologists")
def psychologist_list():
    rep_scores = calculate_psychologist_reputation()
    psychologists = Users.query.filter_by(occupation="psychologist").all()
    # присвоїти рейтинги з rep_scores
    for p in psychologists:
        p.rating = rep_scores.get(p.id, 0.0)
    # сортування
    psychologists_sorted = sorted(psychologists, key=lambda p: p.rating, reverse=True)
    return render_template("psychologists.html", psychologists=psychologists_sorted)

@app.route("/questionnaire", methods=["GET", "POST"])
def questionnaire():
    user = Users.query.filter_by(username=session['user']).first()
    # if request.method == "POST":
    #     answers = json.loads(request.form["answers_json"])
    #     print("Отримані відповіді:", answers)
    #     q = Questionnaire.query.filter_by(user_id=user.id).first()
    #     if not q:
    #         q = Questionnaire(user_id=user.id)
    #         db.session.add(q)

    #     q.prefers_gender = answers.get("gender")
    #     q.prefers_method = answers.get("method")
    #     q.prefers_age_group = answers.get("age")
    #     db.session.commit()

    #     return redirect(url_for("main"))
    
    user = Users.query.filter_by(username=session['user']).first()
    return render_template("questions.html", occupation=user.occupation)


@app.route("/psychologist/<int:id>", methods=["GET", "POST"])
def view_psychologist(id):
    user = Users.query.filter_by(username=session['user']).first()
    psychologist = Users.query.get(id)

    if request.method == "POST":
        score = float(request.form["rating"])
        existing = Rating.query.filter_by(user_id=user.id, psychologist_id=id).first()
        if existing:
            existing.score = score
        else:
            rating = Rating(user_id=user.id, psychologist_id=id, score=score)
            db.session.add(rating)
        db.session.commit()
        return redirect(url_for("psychologist_list"))

    return render_template("profile.html", psychologist=psychologist)

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
