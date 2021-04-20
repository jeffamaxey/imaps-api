import jwt
import time
import os
from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from core.models import *

class UserCreationTests(TestCase):

    def test_can_create_user(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertIsNone(user.last_login)
        self.assertEqual(str(user), "John Locke (locke)")
        self.assertEqual(user.password, "")
        self.assertEqual(user.password_reset_token, "")
        self.assertEqual(user.password_reset_token_expiry, 0)
        self.assertLess(abs(time.time() - user.created), 1)
        self.assertEqual(user.company, "")
        self.assertEqual(user.department, "")
        self.assertEqual(user.location, "")
        self.assertEqual(user.lab, "")
        self.assertEqual(user.job_title, "")
        self.assertFalse(user.groups.count())
        self.assertFalse(user.collections.count())
        self.assertFalse(user.samples.count())
        self.assertFalse(user.executions.count())
        self.assertNotEqual(user.id, 1)
    

    def test_user_uniqueness(self):
        user = mixer.blend(User, username="locke", email="john@gmail.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke2", email="john@gmail.com")
        self.assertEqual(User.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="locke", email="john2@gmail.com")
        self.assertEqual(User.objects.count(), 1)



class UserOrderingTests(TestCase):

    def test_users_ordered_by_created(self):
        user1 = mixer.blend(User, id=2)
        user2 = mixer.blend(User, id=1)
        user3 = mixer.blend(User, id=3)
        self.assertEqual(list(User.objects.all()), [user1, user2, user3])



class UserImageTests(TestCase):

    def setUp(self):
        self.files_at_start = os.listdir("uploads")

    
    def tearDown(self):
        for f in os.listdir("uploads"):
            if f not in self.files_at_start:
                if os.path.exists(os.path.join("uploads", f)):
                    os.remove(os.path.join("uploads", f))


    def test_can_set_image(self):
        user = mixer.blend(User)
        self.assertEqual(user.image, "")
        user.image = SimpleUploadedFile("file.png", b"\x00\x01")
        user.save()
        self.assertTrue(user.image.name.startswith(str(user.id)))
        self.assertTrue(user.image.name.endswith("bVXNlcg.png"))


        
class UserPasswordTests(TestCase):

    def test_can_set_password(self):
        user = User.objects.create(
            username="locke", email="john@gmail.com", name="John Locke",
        )
        self.assertEqual(user.password, "")
        user.set_password("sw0rdfish123")
        self.assertNotEqual(user.password, "sw0rdfish")
        algorithm, iterations, salt, hash_ = user.password.split("$")
        self.assertGreaterEqual(int(iterations), 100000)



class UserTokenTests(TestCase):

    def test_access_jwt_creation(self):
        user = mixer.blend(User)
        token = user.make_access_jwt()
        token = jwt.decode(token, settings.SECRET_KEY)
        self.assertEqual(token["sub"], user.id)
        self.assertLessEqual(time.time() - token["iat"], 2)
        self.assertLessEqual(time.time() - token["expires"] - 900, 2)
    

    def test_refresh_jwt_creation(self):
        user = mixer.blend(User)
        token = user.make_refresh_jwt()
        token = jwt.decode(token, settings.SECRET_KEY)
        self.assertEqual(token["sub"], user.id)
        self.assertLessEqual(time.time() - token["iat"], 2)
        self.assertLessEqual(time.time() - token["expires"] - 31536000, 2)



class UserFromTokenTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)


    def test_no_token_returns_no_user(self):
        self.assertIsNone(User.from_token(None))
    

    def test_invalid_token_returns_no_user(self):
        self.assertIsNone(User.from_token("sdsfsfd"))
    

    def test_expired_token_returns_no_user(self):
        token = jwt.encode({
            "sub": self.user.id, "expires": 100, "iat": 1000000000000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertIsNone(User.from_token(token))
    

    def test_unknown_user_token_returns_no_user(self):
        token = jwt.encode({
            "sub": 23, "expires": 1000000000000, "iat": 100
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertIsNone(User.from_token(token))
    

    def test_valid_token_returns_user(self):
        token = jwt.encode({
            "sub": self.user.id, "expires": 1000000000000, "iat": 100
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.assertEqual(User.from_token(token), self.user)



class UserObjectsAccessTests(TestCase):

    def test_user_groups(self):
        user = mixer.blend(User)
        self.assertFalse(user.admin_groups.count())
        self.assertFalse(user.memberships.count())
        self.assertFalse(user.invitations.count())
        self.assertFalse(user.groups.count())
        g1, g2, g3 = [mixer.blend(Group) for _ in range(3)]
        link1 = UserGroupLink.objects.create(user=user, group=g1, permission=1)
        link2 = UserGroupLink.objects.create(user=user, group=g2, permission=2)
        link3 = UserGroupLink.objects.create(user=user, group=g3, permission=3)
        self.assertEqual(set(user.admin_groups), {g3})
        self.assertEqual(set(user.memberships), {g2, g3})
        self.assertEqual(set(user.invitations), {g1})
        self.assertEqual(set(user.groups.all()), {g1, g2, g3})
    

    def test_user_collections(self):
        user = mixer.blend(User)
        self.assertFalse(user.owned_collections.count())
        self.assertFalse(user.shareable_collections.count())
        self.assertFalse(user.editable_collections.count())
        self.assertFalse(user.collections.count())
        c1, c2, c3, c4 = [mixer.blend(Collection) for _ in range(4)]
        link1 = CollectionUserLink.objects.create(user=user, collection=c1, permission=1)
        link2 = CollectionUserLink.objects.create(user=user, collection=c2, permission=2)
        link3 = CollectionUserLink.objects.create(user=user, collection=c3, permission=3)
        link4 = CollectionUserLink.objects.create(user=user, collection=c4, permission=4)
        self.assertEqual(set(user.owned_collections), {c4})
        self.assertEqual(set(user.shareable_collections), {c3, c4})
        self.assertEqual(set(user.editable_collections), {c2, c3, c4})
        self.assertEqual(set(user.collections.all()), {c1, c2, c3, c4})
    

    def test_user_samples(self):
        user = mixer.blend(User)
        self.assertFalse(user.shareable_samples.count())
        self.assertFalse(user.editable_samples.count())
        self.assertFalse(user.samples.count())
        s1, s2, s3, = [mixer.blend(Sample) for _ in range(3)]
        link1 = SampleUserLink.objects.create(user=user, sample=s1, permission=1)
        link2 = SampleUserLink.objects.create(user=user, sample=s2, permission=2)
        link3 = SampleUserLink.objects.create(user=user, sample=s3, permission=3)
        self.assertEqual(set(user.shareable_samples), {s3})
        self.assertEqual(set(user.editable_samples), {s2, s3})
        self.assertEqual(set(user.samples.all()), {s1, s2, s3})
    

    def test_user_executions(self):
        user = mixer.blend(User)
        self.assertFalse(user.owned_executions.count())
        self.assertFalse(user.shareable_executions.count())
        self.assertFalse(user.editable_executions.count())
        self.assertFalse(user.executions.count())
        e1, e2, e3, e4 = [mixer.blend(Execution) for _ in range(4)]
        link1 = ExecutionUserLink.objects.create(user=user, execution=e1, permission=1)
        link2 = ExecutionUserLink.objects.create(user=user, execution=e2, permission=2)
        link3 = ExecutionUserLink.objects.create(user=user, execution=e3, permission=3)
        link4 = ExecutionUserLink.objects.create(user=user, execution=e4, permission=4)
        self.assertEqual(set(user.owned_executions), {e4})
        self.assertEqual(set(user.shareable_executions), {e3, e4})
        self.assertEqual(set(user.editable_executions), {e2, e3, e4})
        self.assertEqual(set(user.executions.all()), {e1, e2, e3, e4})