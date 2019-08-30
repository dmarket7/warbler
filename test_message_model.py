from app import app
"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserMessageTestCase(TestCase):
    """Test model for Messages"""

    def setUp(self):
        """Set up our test cases"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user1 = User.signup(
            email="user@email.com",
            username="username",
            password="password",
            image_url=None
        )
        user2 = User.signup(
            email="user2@email.com",
            username="username2",
            password="password2",
            image_url=None
        )
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

    def tearDown(self):
        """Idk what this is suppose to do tbh"""
        pass
    
    def test_mesage_model(self):
        """Testing basic Message Model"""
        msg = Message
