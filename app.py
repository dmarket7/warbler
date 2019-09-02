import os

from flask import Flask, render_template, request, flash, redirect, session, g
# from flask_admin import Admin
# from flask_basicauth import BasicAuth
from flask_login import LoginManager
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from forms import MessageForm, UserAddForm, EditUserForm, LoginForm
from models import db, connect_db, User, Message, Follows, Like


CURR_USER_KEY = "curr_user"


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

# Implement Flask-Admin
# basic_auth = BasicAuth(app)

# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
# app.config['BASIC_AUTH_USERNAME'] = 'patrickstar'
# app.config['BASIC_AUTH_PASSWORD'] = 'password'
# app.config['BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD'] = True

# admin = Admin(app, name='warbler', template_mode='bootstrap3')
# Add administrative views here

# app.run()

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
# app.config['SQLALCHEMY_DATABASE_URI'] = (
    # os.environ.get('postgres://ozibortidvmjrz:11d564c5697d2a82c86fbe8f0c479ac0ba5e3ffa013cd4bef7eca7c4d8f555f9@ec2-54-83-33-14.compute-1.amazonaws.com:5432/dedtj3givh6msh', 'postgres:///warbler'))

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    # 'DATABASE_URL', 'postgres:///ozibortidvmjrz:11d564c5697d2a82c86fbe8f0c479ac0ba5e3ffa013cd4bef7eca7c4d8f555f9@ec2-54-83-33-14.compute-1.amazonaws.com:5432/dedtj3givh6msh')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "nevertell")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
# @app.route('/admin')
# @basic_auth.required
# def secret_view():
#     basic_auth.init_app()
#     if basic_auth.check_credentials(g.user.username, g.user.password):
#         return render_template('admin/master.html')
#     else:
#         return "Not authorized!"    

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    return redirect('/')
    # IMPLEMENT THIS


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())

    g_likes = [msg.id for msg in g.user.likes]
    # import pdb; pdb.set_trace()
    return render_template('users/show.html', user=user, messages=messages, user_likes=g_likes)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(request.referrer)


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(request.referrer)


# Route for displaying liked posts
@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    user_likes = [msg.id for msg in user.likes]

    return render_template('users/likes.html', user=user, user_likes=user_likes)


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(g.user.id)
    form = EditUserForm(obj=user)

    if form.validate_on_submit():

        # Grabbing our form data
        username = form.username.data
        email = form.email.data
        bio = form.bio.data
        location = form.location.data
        image = form.image_url.data
        header_image = form.header_image.data

        # Setting our images to None
        if header_image == "":
            header_image = None
        if image == "":
            image = None

        # Authenticating our user
        auth_user = User.authenticate(g.user.username,
                                      form.password.data)
        if auth_user:
            try:
                auth_user.username = username
                auth_user.email = email
                auth_user.bio = bio
                auth_user.location = location
                auth_user.image_url = image
                auth_user.header_image_url = header_image

                db.session.add(auth_user)
                db.session.commit()

                return redirect(f'/users/{auth_user.id}')
 
            except (IntegrityError, InvalidRequestError):
                db.session.rollback()
                user_email = User.query.filter(User.email == email).first()
                user_username = User.query.filter(User.username == username).first()
                if user_email and user_username and (user_username.username != auth_user.username) and (user_email.email != auth_user.email):
                    # import pdb; pdb.set_trace()
                    text = "Email and Username already exist"
                elif user_email and (user_email.email != auth_user.email):
                    text = "Email already exists"
                else:
                    text = "Username already exists"
                
                flash(f"{text}", category='user-edit')
                return redirect('/users/profile')

        else:
            flash("Invalid password", category='user-edit')
            return redirect('/users/profile')

    return render_template('users/edit.html', form=form, user=user)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/likes/<int:message_id>', methods=["POST"])
def like_message(message_id):
    """Like a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    try:
        cur_message = Message.query.get(message_id)
        if cur_message.user_id == g.user.id:
            return redirect(request.referrer)
        like = Like(msg_id=message_id, user_id=g.user.id)
        db.session.add(like)
        db.session.commit()
        g_likes = [msg.id for msg in g.user.likes]
        return redirect(request.referrer)

    except (IntegrityError, InvalidRequestError):
        db.session.rollback()
        liked_msg = Like.query.get_or_404((g.user.id, message_id))
        db.session.delete(liked_msg)
        db.session.commit()
        g_likes = [msg.id for msg in g.user.likes]

        return redirect(request.referrer)

##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    if g.user:
        following_ids = [user.id for user in g.user.following]

        messages = (Message
                    .query
                    .filter(db.or_(
                        Message.user_id.in_(following_ids),
                        Message.user_id == g.user.id
                    ))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        # users = [m.user for m in messages]
        g_likes = [msg.id for msg in g.user.likes]
        return render_template('home.html', messages=messages, user_likes=g_likes)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
