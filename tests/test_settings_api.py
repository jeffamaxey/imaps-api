from execution.models import Execution
import os
from django.contrib.auth.hashers import check_password
from core.models import User, Group, UserGroupLink
from analysis.models import Collection, CollectionUserLink
from execution.models import Execution, ExecutionUserLink
from .base import FunctionalTest

class PasswordUpdateTests(FunctionalTest):

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



class UserModificationTests(FunctionalTest):

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



class UserImageEditingTests(FunctionalTest):

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



class UserDeletionTests(FunctionalTest):

    def test_can_delete_account(self):
        # There's a group for which the user is the only member
        UserGroupLink.objects.create(user=self.user, group=Group.objects.create(), permission=2)

        # There's a group that the user is the admin of, with another admin
        group = Group.objects.create(slug=".")
        user2 = User.objects.create(username="u2")
        UserGroupLink.objects.create(user=self.user, group=group, permission=3)
        UserGroupLink.objects.create(user=user2, group=group, permission=3)

        # User owns a collection with someone else
        collection = Collection.objects.create(name="C1")
        CollectionUserLink.objects.create(user=self.user, collection=collection, permission=4)
        CollectionUserLink.objects.create(user=user2, collection=collection, permission=4)

        # User owns an execution with someone else
        execution = Execution.objects.create(name="E1")
        ExecutionUserLink.objects.create(user=self.user, execution=execution, permission=4)
        ExecutionUserLink.objects.create(user=user2, execution=execution, permission=4)

        # Send deletion mutation
        users_at_start = User.objects.count()
        result = self.client.execute("""mutation { deleteUser { success } }""")

        # It works
        self.assertTrue(result["data"]["deleteUser"]["success"])
        self.assertEqual(User.objects.count(), users_at_start - 1)
        self.assertFalse(User.objects.filter(username="jack").count())
    

    def test_account_deletion_can_fail(self):
        users_at_start = User.objects.count()

        # Would leave groups with no admin
        group = Group.objects.create(name="G1")
        UserGroupLink.objects.create(user=self.user, group=group, permission=3)
        self.check_query_error("""mutation { deleteUser { success } }""", message="only admin")
        self.assertEqual(User.objects.count(), users_at_start)
        group.delete()

        # Would leave collections without owner
        collection = Collection.objects.create(name="C1")
        CollectionUserLink.objects.create(user=self.user, collection=collection, permission=4)
        self.check_query_error("""mutation { deleteUser { success } }""", message="collection")
        self.assertEqual(User.objects.count(), users_at_start)
        collection.delete()

        # Would leave executions without owner
        execution = Execution.objects.create(name="E1")
        ExecutionUserLink.objects.create(user=self.user, execution=execution, permission=4)
        self.check_query_error("""mutation { deleteUser { success } }""", message="execution")
        self.assertEqual(User.objects.count(), users_at_start)
        execution.delete()

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



class UserLeavingGroupTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="Adam Group", slug="adam-group", description="Adam's Group"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=2)
        user2 = User.objects.create(username="user2", email="user2@gmail.com")
        UserGroupLink.objects.create(user=user2, group=self.group, permission=2)


    def test_can_leave_group(self):
        # Leave group
        result = self.client.execute(
            """mutation { leaveGroup(id: "1") { 
                group { users { username } }
                user { username email name }
             } }"""
        )

        # User is no longer in group
        self.assertEqual(result["data"]["leaveGroup"]["group"], {"users": [
            {"username": "user2"}
        ]})
        self.assertEqual(self.user.groups.count(), 0)
        self.assertEqual(result["data"]["leaveGroup"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_leave_group_if_not_appropriate(self):
        Group.objects.create(id=2, slug="new-group")
        # Not in group
        self.check_query_error(
            """mutation { leaveGroup(id: "2") { group { name } } }""",
            message="Not in group"
        )

        # Group doesn't exist
        self.check_query_error(
            """mutation { leaveGroup(id: "20") { group { name } } }""",
            message="Does not exist"
        )

        # Would be no admins
        self.link.permission = 3
        self.link.save()
        self.check_query_error(
            """mutation { leaveGroup(id: "1") { group { name } } }""",
            message="no admins"
        )


    def test_cant_leave_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { leaveGroup(id: "1") { group { name } } }""",
            message="Not authorized"
        )