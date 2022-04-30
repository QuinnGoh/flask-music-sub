from flask import Flask, render_template, request, session, redirect
from models import User
from util import database, put_user, create_user_music_table, check_credentials, add_user_music_table, \
    retrieve_user_table, get_user_id, remove_user_music_table, query, check_exist_email, get_user_name

app = Flask(__name__, template_folder="templates")

# INSTANTIATE DATABASE INSTANCE
database = database()

# SECRET KEY FOR SESSION - SHOULD BE MOVED TO CONFIG FILES
app.secret_key = 'dhfgdufhgeh2837'


# PUTS USER INTO DYNAMODB
def register_user(_email, _user_name, _password):
    put_user(User(_user_name, _email, _password))

    return redirect('/login')


# REGISTER PAGE AND FUNCTIONALITY
@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []

    if request.method == 'POST':
        _email = request.form['email']
        _username = request.form['username']
        _password = request.form['password']

        if check_exist_email(_email):
            errors.append("Email")

        if not errors:

            if register_user(_email, _username, _password):
                create_user_music_table(str(hash(_email)))
                return redirect('/login')
        else:
            return render_template('register.html', errors=errors)

    return render_template('register.html', errors=errors)


# DASHBOARD PAGE AND FUNCTIONALITY (CONTAINS POSTS)
@app.route('/dashboard', methods=['GET', 'POST'])
def home():
    query_results = []
    dynamo_resp = " "

    # CHECK USER HAS LOGGED IN
    if not session.get('user_name'):
        return redirect('/login')
    else:
        subscriptions = retrieve_user_table(session['user_id'])

        if not subscriptions:
            dynamo_resp = "noSubscriptions"

    # POST CONTENT FROM HTML FORM
    if request.method == 'POST':

        if request.form['submit_button'] == "query":

            artist = None
            title = None
            year = None
            function = ""

            if request.form['artist']:
                function = function + 'a'
                artist = request.form['artist']

            if request.form['title']:
                function = function + 't'
                title = request.form['title']

            if request.form['year']:
                function = function + 'y'
                year = request.form['year']

            query_results = query(function, artist, title, year)

            if not query_results:
                dynamo_resp = "noResults"

        if request.form['submit_button'].endswith("_subscribe_"):
            song_details = request.form['submit_button'].split(",")
            img_url = song_details[0]
            year = song_details[1]
            title = song_details[2]
            artist = song_details[3]

            add_user_music_table(img_url, year, title, artist, session['user_id'])

            return redirect('/dashboard')

        if request.form['submit_button'].endswith("_remove_"):
            song_details = request.form['submit_button'].split("_")
            title = song_details[0]
            #
            remove_user_music_table(title, session['user_id'])
            #
            return redirect('/dashboard')

    return render_template('dashboard.html', songs=query_results, subscriptions=subscriptions,
                           user_name=session['user_name'], dynamo_resp=dynamo_resp)


# LOGIN PAGE AND FUNCTIONALITY
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    # CHECK USER HAS LOGGED IN
    if session.get('user_name') and session.get('email'):
        return redirect('/dashboard')
    if request.method == 'POST':

        _email = request.form['email']
        _password = request.form['password']

        if check_credentials(_email, _password):
            session['email'] = _email
            session['user_name'] = get_user_name(_email)
            session['user_id'] = get_user_id(_email)
            return redirect('/dashboard')
        else:
            error = True

    return render_template('login.html', error=error)


@app.route('/')
def index():
    return redirect('/dashboard')


# CLEARS SESSION AND RETURNS TO LOGIN PAGE
@app.route('/logout')
def logout():
    if session['user_name']:
        session.clear()

    return redirect('/login')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
