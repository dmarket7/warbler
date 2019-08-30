"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Like, connect_db

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app
from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for Users"""

    def setUp(self):
        """Create test client, add sample data"""

        User.query.delete()
        Message.query.delete()
        
        self.client = app.test_client()

        self.testuser = User.signup(username="username",
                                    email="username@email.com",
                                    password="password",
                                    image_url=None)
        db.session.commit()


    def test_create_user(self):
        """Can we add a user?"""

        self.client = app.test_client()
        # import pdb; pdb.set_trace()        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/signup", data={"username": "patrickstar",
                                            "email": "patrickstar@email.com",
                                            "password": "password",
                                            "image_url": None
                                            })   

            self.assertEqual(resp.status_code, 302)

            user = User.query.filter_by(username="patrickstar").first()

            self.assertEqual(user.username, "patrickstar")
            