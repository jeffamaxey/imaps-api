import os
from django.contrib.auth.hashers import check_password
from core.models import *
from .base import FunctionalTest

class SettingsApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
        )
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        self.user.set_password("livetogetha")



class PasswordUpdateTests(SettingsApiTests):

    def test_can_update_password(self):
        # Send new password
        result = self.client.execute("""mutation { updatePassword(
            current: "livetogetha", new: "warwick96"
        ) { success } }""")

        # Password is changed
        self.assertEqual(result["data"], {"updatePassword": {"success": True}})
        self.user.refresh_from_db()
        self.assertTrue(check_password("warwick96", self.user.password))
    

    def test_can_validate_updated_password(self):
        # Password must be 9 or more characters
        self.check_query_error("""mutation { updatePassword(
            current: "livetogetha", new: "arwick96"
        ) { success } }""", message="too short")
        self.user.refresh_from_db()
        self.assertFalse(check_password("arwick96", self.user.password))
        self.assertTrue(check_password("livetogetha", self.user.password))

        # Password can't be numeric
        self.check_query_error("""mutation { updatePassword(
            current: "livetogetha", new: "27589234759879230"
        ) { success } }""", message="numeric")
        self.user.refresh_from_db()
        self.assertFalse(check_password("27589234759879230", self.user.password))
        self.assertTrue(check_password("livetogetha", self.user.password))

        # Password must be reasonably uncommon
        self.check_query_error("""mutation { updatePassword(
            current: "livetogetha", new: "password1"
        ) { success } }""", message="too common")
        self.user.refresh_from_db()
        self.assertFalse(check_password("password1", self.user.password))
        self.assertTrue(check_password("livetogetha", self.user.password))

        # Password must be correct
        self.check_query_error("""mutation { updatePassword(
            current: "livetogetha123", new: "warwick96"
        ) { success } }""", message="password not correct")
        self.user.refresh_from_db()
        self.assertFalse(check_password("warwick96", self.user.password))
        self.assertTrue(check_password("livetogetha", self.user.password))

        # Token must be given
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updatePassword(
            current: "livetogetha", new: "warwick96"
        ) { success } }""", message="Not authorized")



class UserModificationTests(SettingsApiTests):

    def test_can_update_user_info(self):
        # Update info
        result = self.client.execute("""mutation { updateUser(
            email: "jack@island.com", username: "dr_j", name: "Dr Jack"
        ) { user { email username name } } }""")

        # The new user info is returned
        self.assertEqual(result["data"]["updateUser"]["user"], {
            "email": "jack@island.com", "name": "Dr Jack", "username": "dr_j"
        })

        # The user has updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jack@island.com")
        self.assertEqual(self.user.username, "dr_j")
        self.assertEqual(self.user.name, "Dr Jack")
    

    def test_cant_edit_user_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateUser(
            email: "jack@island.com", username: "dr_j", name: "Dr Jack"
        ) { user { email username name } } }""", message="Not authorized")



class UserImageEditingTests(SettingsApiTests):

    def test_can_edit_image(self):
        # Update info
        with open(os.path.join("tests", "files", "user-icon.png"), "rb") as f:
            result = self.client.execute("""mutation updateImage($image: Upload!) {
                updateUserImage(image: $image) { user { username image } }
            }""", variables={"image": f})

        # The new user info is returned
        image = result["data"]["updateUserImage"]["user"]["image"]
        self.assertTrue(image.endswith("png"))
        self.assertTrue(len(image) > 10)

        # The photo is actually saved
        self.assertIn(image, os.listdir("uploads"))
        self.assertEqual(len(self.files_at_start) + 1, len(os.listdir("uploads")))
        with open(os.path.join("tests", "files", "user-icon.png"), "rb") as f1:
            with open(os.path.join("uploads", image), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

        # The image can be changed to another image
        with open(os.path.join("tests", "files", "user-icon-2.jpg"), "rb") as f:
            result = self.client.execute("""mutation updateImage($image: Upload!) {
                updateUserImage(image: $image) { user { username image } }
            }""", variables={"image": f})
        
        # The new user info is returned
        image2 = result["data"]["updateUserImage"]["user"]["image"]
        self.assertTrue(image2.endswith("jpg"))
        self.assertTrue(len(image2) > 10)
        self.assertNotEqual(image, image2)
        self.assertEqual(len(image), len(image2))

        # The photo is actually saved and replaces the old one
        self.assertIn(image2, os.listdir("uploads"))
        self.assertEqual(len(self.files_at_start) + 1, len(os.listdir("uploads")))
        with open(os.path.join("tests", "files", "user-icon-2.jpg"), "rb") as f1:
            with open(os.path.join("uploads", image2), "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

        # The image can be removed
        result = self.client.execute("""mutation updateImage($image: Upload!) {
            updateUserImage(image: $image) { user { username image } }
        }""", variables={"image": ""})

        # The new user info is returned
        self.assertEqual(result["data"]["updateUserImage"]["user"]["image"], "")

        # The photos are gone
        self.assertEqual(len(self.files_at_start), len(os.listdir("uploads")))
    

    def test_cant_edit_user_image_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateUserImage(image: "") {
            user { email username name } }
        }""", message="Not authorized")



class UserDeletionTests(SettingsApiTests):

    def test_can_delete_account(self):
        # Allowable user connections
        user2 = User.objects.create(username="u2")
        collection = Collection.objects.create(name="C1")
        CollectionUserLink.objects.create(user=self.user, collection=collection, is_owner=True)
        CollectionUserLink.objects.create(user=user2, collection=collection, is_owner=True)
        group = Group.objects.create(name="G1")
        group.admins.add(self.user)
        group.admins.add(user2)

        # Send deletion mutation
        users_at_start = User.objects.count()
        result = self.client.execute("""mutation { deleteUser { success } }""")

        # It works
        self.assertTrue(result["data"]["deleteUser"]["success"])
        self.assertEqual(User.objects.count(), users_at_start - 1)
        self.assertFalse(User.objects.filter(username="jack").count())
    

    def test_account_deletion_can_fail(self):
        users_at_start = User.objects.count()

        # Would leave collections without owner
        collection = Collection.objects.create(name="C1")
        CollectionUserLink.objects.create(user=self.user, collection=collection, is_owner=True)
        self.check_query_error("""mutation { deleteUser { success } }""", message="collection")
        self.assertEqual(User.objects.count(), users_at_start)
        collection.delete()

        # Would leave groups with no admin
        group = Group.objects.create(name="G1")
        group.admins.add(self.user)
        self.check_query_error("""mutation { deleteUser { success } }""", message="only admin")
        self.assertEqual(User.objects.count(), users_at_start)

        # Invalid token
        self.client.headers["Authorization"] = "Bearer qwerty"
        self.check_query_error(
            """mutation { deleteUser { success } }""",
            message="Invalid or missing token"
        )
        self.assertEqual(User.objects.count(), users_at_start)

        # No token
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteUser { success } }""",
            message="Invalid or missing token"
        )
        self.assertEqual(User.objects.count(), users_at_start)

