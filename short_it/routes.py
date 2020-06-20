from flask import render_template, url_for, jsonify, redirect, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from short_it import app, db, bcrypt
from short_it.models import URL, User
from short_it.forms import LoginForm, RegistrationForm, ShortenForm
from short_it.shortener import random_url_gen


# Route for home page
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@app.route("/home", methods=["GET"])
def index():
    # If the user is already logged in and
    # hence has user id stored in the session,
    # then we redirect this individual back to
    # index page
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html", title="Home")


# Rotue for shorten page
@app.route("/shorten", methods=["GET", "POST"])
def shorten():
    # create oboject of the WTForm to be used
    # by end users to add in the original and
    # the (optional) shortened URL
    form = ShortenForm()

    # Handling POST requests; in this case the
    # only POST request to be recieved is that
    # of a form submission
    # Hence all other POST requests will return
    # and render the default web page for the route
    if request.method == "POST" and form.validate_on_submit():
        # This block of code checks whether the
        # form data entered by the user has the
        # optional shortened url data or not
        # If it does not have the shortened url data,
        # then it is generated by the random_url_gen function
        if not form.shortened_url.data:
            shortened_url = random_url_gen()
        else:
            shortened_url = form.shortened_url.data

        # Creating an URL object to store the
        # original url data (recieved from the WTForm)
        # along with the shortened url data
        new_shortened_url = URL(
            original_url=form.original_url.data,
            shortened_url=shortened_url,
        )
        new_shortened_url.save()  # Adding the URL object to the database

        # Since any individual can shorten any link they
        # want, but only registered users can access
        # information such as user hits, user locations, etc.
        # relevant to the shortened URLs, this block of code
        # checks whether a session has a user logged in or not
        # If a user is logged in, then the ID of the URL object
        # is stored in a field of the document belonging to the
        # current user
        if current_user.is_authenticated:
            user = User.objects(id=current_user.id).first()
            user.update(push__url_list=URL.objects(
                shortened_url=shortened_url).first().id)

        flash("localhost:5000/"+str(shortened_url), "primary")
    return render_template("shorten.html", title="Short-It", form=form)


# Rotue for redirecting a shortened URL call
# to the original URL
@app.route("/<string:url_id>")
def shortened(url_id):
    # This block of code redirects the end user
    # to the desired location, if there exists a
    # short => long mapping
    # Otherwise, a flash message is generated

    # NOTE: Try generating a custom error page
    # rather than a flash message (Take someone's
    # opinion regarding this idea)
    objects = URL.objects(shortened_url=url_id)
    if len(objects) == 1:
        url_object = objects[0]
        url_object.update(inc__counter=1)
        url_object.update(push__date_array=datetime.utcnow)
        original_url = url_object.original_url
        return redirect(original_url)

    flash("The URL does not exist", "danger")
    return redirect(url_for("index"))


# Rotue to access the dashboard which
# stores all the information pertaining
# to shortened URLs
# Is only accessible by registered users
@app.route("/dashboard")
@login_required
def dashboard():
    # TODO: Acquire information for all the
    # links belonging to the end user and display
    # these stats
    return render_template("dashboard.html")


# Rotue to access the login page
@app.route("/login", methods=["GET", "POST"])
def login():
    # If the user is already logged in and
    # hence has user id stored in the session,
    # then we redirect this individual back to
    # index page
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    # create oboject of the WTForm to be used
    # by end users to add in the original and
    # the (optional) shortened URL
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        # Acquire user object based on form data
        user = User.objects(user_name=form.user_name.data)
        if len(user) == 1 and bcrypt.check_password_hash(user.first().password, form.password.data):
            # if information matches, log the user in
            login_user(user=user.first())
            flash("You were successfully logged in!", "success")

            # If the login is a result of a redirection due to
            # end user trying to access a route with login required,
            # we redirect the user to that initial route
            if request.args.get('next'):
                return redirect(request.args.get('next'))

            return redirect(url_for("index"))
        flash("Login unsuccessful", "danger")

    return render_template("login.html", title="Login", form=form)


# Rotue to access the registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if request.method == "POST" and form.validate_on_submit():

        hashed_password = bcrypt.generate_password_hash(form.password.data)

        new_user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_name=form.user_name.data,
            email=form.email.data,
            password=hashed_password,
        )
        new_user.save()

        flash(
            f"Welcome, {form.user_name.data}! You have been successfully registered as a user of Short It :)", "success")
        return redirect(url_for("index"))

    return render_template("register.html", title="Register", form=form)


# Rotue to logout the user and delete
# the session
@app.route("/logout")
def logout():
    logout_user()
    flash("You were successfully logged out!", "success")
    return redirect(url_for("index"))
