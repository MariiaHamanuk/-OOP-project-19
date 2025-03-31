'''back-end'''
import json
from flask import Flask, render_template, request, redirect, url_for, session



app = Flask(__name__)
app.secret_key = "very_secure123"

DATA = "users_data.json"
EVENTS = "events.json"



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
    data = read_file(DATA)
    occupation = data[0][session['user']]["occupation"]
    return render_template("main.html", occupation=occupation)

@app.route("/calendar")
def calendar():
    '''calendar page'''
    data = read_file(DATA)
    occupation = data[0][session['user']]["occupation"]
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

@app.route('/add-event')
def v_register():
    '''add event page'''
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

#sing up/in

@app.route("/validation", methods=["POST"])
def validate_user():
    '''validates user'''
    username = request.form["username"]
    password = request.form["password"]
    data = read_file(DATA)
    if not username in data[0]:
        return render_template('login.html', error_message="No account with this username")

    if data[0][username]['password'] == password:
        if not "accepted" in data[0][username]:
            session["user"] = username
            return redirect(url_for("main"))
    return render_template("login.html", error_message="Wrong password")

@app.route("/save", methods=["POST"])
def save_data():
    '''saves user to file'''
    occupation = request.form["occupation"]

    username = request.form.get("username")
    params = ["occupation", "password"]

    if occupation == "psychologist":
        params.extend(["name", "surname", "bio", "email", "number", "accepted"])

    elif occupation == "volunteer":
        event = request.form["event-name"]
        info = {"description": request.form['description'], \
"email": request.form['email'], "number": request.form['number']}
        write_to_json(event, info, EVENTS)
        return redirect(url_for("v_approving"))

    info = {param : request.form.get(param, False) for param in params}
    if not used(username):
        write_to_json(username, info, DATA)

        if occupation == "military":
            session["user"] = username
            return redirect(url_for("main"))
        return redirect(url_for("ps_approving"))

    if occupation == "military":
        return render_template("m-register.html", \
error_message="Account with this username already exists")
    return render_template("ps-register.html", \
error_message="Account with this username already exists")

def used(username):
    '''checks if name is already in use'''
    data = read_file(DATA)
    return username in data[0]

def read_file(filename):
    '''loads json file'''
    with open(filename, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = [{}]
    return data

def write_to_json(key, info, filename):
    '''writes data to file'''
    data = read_file(filename)
    data[0][key] = info

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.route("/complete-logout")
def logout():
    '''logout function'''
    session.pop("user",None)
    session.clear()
    return redirect(url_for("start"))

if __name__ == "__main__":
    app.run(debug=True)