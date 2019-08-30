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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Like.query.delete()

        user = User(
            email="patrick@star.com",
            username="patrickstar",
            password="password"
        )

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.likes), 0)

    def test_repr_method(self):
        """Does repr method work?"""

        user = User(
            email="patrick@star.com",
            username="patrickstar",
            password="password"
        )

        db.session.add(user)
        db.session.commit()

        self.assertEqual(
            repr(user), f'<User #{user.id}: patrickstar, patrick@star.com>')

    def test_is_following(self):
        """Testing is_following method"""

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        patrick = User(
            email="patrick@star.com",
            username="patrickstar",
            password="password"
        )

        db.session.add(user)
        db.session.add(patrick)

        db.session.commit()

        # Create relationships on follows
        f = Follows(user_being_followed_id=user.id,
                    user_following_id=patrick.id)

        db.session.add(f)
        db.session.commit()

        # Test if user is following method works
        self.assertEqual(patrick.is_following(user), True)
        self.assertEqual(len(patrick.following), 1)

        # Test if user is not following method works
        self.assertEqual(user.is_following(patrick), False)

    def test_is_followed_by(self):
        """Testing is_followed_by method"""

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        patrick = User(
            email="patrick@star.com",
            username="patrickstar",
            password="password"
        )

        db.session.add(user)
        db.session.add(patrick)

        db.session.commit()

        # patrick is following user
        f = Follows(user_being_followed_id=user.id,
                    user_following_id=patrick.id)

        db.session.add(f)
        db.session.commit()

        self.assertEqual(user.is_followed_by(patrick), True)
        self.assertEqual(patrick.is_followed_by(user), False)

        self.assertEqual(len(user.followers), 1)

    def test_user_signup(self):
        """Testing if user is created"""

        # Assume using the same username
        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url=None
        )
        patrick = User.signup(
            email="patrick@star.com",
            username="testuser2",
            password="password",
            image_url=None
        )

        db.session.add(user)
        db.session.commit()

        db.session.add(patrick)
        db.session.commit()

        user_count = User.query.count()

        self.assertEqual(user_count, 2)

    def test_user_authentication(self):
        """Testing user authentication"""

        patrick = User.signup(
            email="patrick@star.com",
            username="testuser2",
            password="password",
            image_url=None
        )

        db.session.add(patrick)
        db.session.commit()

        auth_user = User.authenticate("testuser2", "password")
        invalid_auth = User.authenticate("testuser2", "not_the_password")

        self.assertTrue(auth_user)
        self.assertFalse(invalid_auth)
