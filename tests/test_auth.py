import kirjava
import base64
import requests
import jwt
import json
import time
import os
import re
from django.conf import settings
from django.core import mail
from django.contrib.auth.hashers import check_password
from .base import FunctionalTest, TokenFunctionaltest
from core.models import User, Group, GroupInvitation

class UserQueryTests(TokenFunctionaltest):

    
    def test_can_get_other_user(self):
        # Get user
        del self.client.headers["Authorization"]
        result = self.client.execute("""{ user(username: "boone") {
            username email name lastLogin creationTime
            groups { name } adminGroups { name } invitations { group { name } }
            collections { name } ownedCollections { name } allCollections { name }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["user"], {
            "username": "boone", "email": "boone@gmail.com",
            "name": "Boone Carlyle", "lastLogin": None, "creationTime": 946684801,
            "groups": [{"name": "Shephard Lab"}],
            "adminGroups": None, "invitations": None,
            "collections": [{"name": "Experiment 1"}],
            "ownedCollections": [],
            "allCollections": [{"name": "Experiment 1"}],
        })
    

    def test_can_get_users(self):
        # Get user
        result = self.client.execute("""{ users {
            username email name
        } }""")
        self.assertEqual(result["data"]["users"], [
            {"username": "ben", "email": "ben@gmail.com", "name": "Ben Linus"},
            {"username": "juliette", "email": "juliette@gmail.com", "name": "Juliette Burke"},
            {"username": "ethan", "email": "ethan@gmail.com", "name": "Ethan Rom"},
            {"username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"},
            {"username": "boone", "email": "boone@gmail.com", "name": "Boone Carlyle"},
            {"username": "shannon", "email": "shannon@gmail.com", "name": "Shannon Rutherford"}
        ])
    

    def test_invalid_user_requests(self):
        # Incorrect username
        self.check_query_error("""{ user(username: "smoke") {
            name username
        } }""", message="Does not exist")
    

    def test_must_be_logged_in_to_get_self_user(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""{ user {
            username email name lastLogin
        } }""", message="Not authorized")


    def test_can_get_group(self):
        # Get group
        result = self.client.execute("""{ group(slug: "others") {
            name slug description users { username } admins { username }
            invitations { user { username } } userCount
            collections { name }
            allCollections { edges { node { name } } } allCollectionsCount
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["group"], {
            "name": "The Others", "description": "", "slug": "others",
            "users": [
                {"username": "ben"}, {"username": "juliette"},
                {"username": "ethan"}, {"username": "jack"}
            ],
            "admins": [{"username": "ben"}],
            "invitations": [{"user": {"username": "jack"}}],
            "userCount": 4,
            "collections": [{"name": "Experiment 4"}],
            "allCollections": {"edges": [
                {"node": {"name": "Experiment 2"}}, {"node": {"name": "Experiment 4"}}
            ]},
            "allCollectionsCount": 2
        })

        # Paginated all collections
        result = self.client.execute("""{ group(slug: "others") {
            allCollections(offset: 1, first: 1) { edges { node { name } } } allCollectionsCount
        } }""")
        self.assertEqual(result["data"]["group"], {
            "allCollections": {"edges": [{"node": {"name": "Experiment 4"}}]},
            "allCollectionsCount": 2
        })


        # Can't get all collections if not in group or logged out though
        Group.objects.get(id=2).users.remove(self.user)
        result = self.client.execute("""{ group(slug: "others") {
            allCollections { edges { node { name } } } allCollectionsCount
        } }""")
        self.assertEqual(result["data"]["group"], { "allCollections": {"edges": []}, "allCollectionsCount": 0})
        Group.objects.get(id=2).users.add(self.user)
        del self.client.headers["Authorization"]
        result = self.client.execute("""{ group(slug: "others") {
            allCollections { edges { node { name } } } allCollectionsCount
        } }""")
        self.assertEqual(result["data"]["group"], { "allCollections": {"edges": []}, "allCollectionsCount": 0})

    

    def test_invalid_group_requests(self):
        # Incorrect ID
        self.check_query_error("""{ group(slug: "XYZ") {
            name description
        } }""", message="Does not exist")



class PasswordUpdateTests(TokenFunctionaltest):

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




        


    
class UserModificationTests(TokenFunctionaltest):

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



class UserImageEditingTests(TokenFunctionaltest):

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

            

class UserDeletionTests(TokenFunctionaltest):

    def test_can_delete_account(self):
        # Send deletion mutation
        self.user.collections.first().delete()
        Group.objects.get(name="Shephard Lab").admins.add(User.objects.get(username="boone"))
        users_at_start = User.objects.count()
        result = self.client.execute("""mutation { deleteUser { success } }""")

        # It works
        self.assertTrue(result["data"]["deleteUser"]["success"])
        self.assertEqual(User.objects.count(), users_at_start - 1)
        self.assertFalse(User.objects.filter(username="jack").count())
    

    def test_account_deletion_can_fail(self):
        users_at_start = User.objects.count()
        Group.objects.get(name="Shephard Lab").admins.add(User.objects.get(username="boone"))

        # Own collections
        self.check_query_error("""mutation { deleteUser { success } }""", message="collection")
        self.assertEqual(User.objects.count(), users_at_start)
        self.user.collections.first().delete()

        # Would leave orphan groups
        Group.objects.get(name="Shephard Lab").admins.remove(User.objects.get(username="boone"))
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



class GroupCreationTests(TokenFunctionaltest):

    def test_can_create_group(self):
        # User creates a group
        result = self.client.execute("""mutation { createGroup(
            name: "A Team", slug: "a_team" description: "The A Team"
        ) {
            group { name slug description users { username } admins { username } }
            user { username email name }
        } }""")

        # The group is returned
        self.assertEqual(result["data"]["createGroup"]["group"], {
            "name": "A Team", "description": "The A Team", "slug": "a_team",
            "users": [{"username": "jack"}], "admins": [{"username": "jack"}]
        })
        self.assertEqual(result["data"]["createGroup"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })

        # The user can access their groups
        result = self.client.execute("""{ user {
            username groups { name } adminGroups { name }
        } }""")
        self.assertEqual(result["data"]["user"], {
            "username": "jack",
            "groups": [{"name": "Shephard Lab"}, {"name": "A Team"}, {"name": "The Others"}],
            "adminGroups": [{"name": "Shephard Lab"}, {"name": "A Team"}],
        })
    

    def test_group_creation_validation(self):
        # Name must be unique
        self.check_query_error("""mutation { createGroup(
            name: "Others", description: "The A Team", slug: "others"
        ) { group { name description users { username } admins { username } } } }""",
        message="already exists")


    def test_must_be_logged_in_to_create_group(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { createGroup(
            name: "A Team", description: "The A Team", slug: "a_team"
        ) { group { name description users { username } admins { username } } } }""",
        message="Not authorized")



class GroupUpdatingTests(TokenFunctionaltest):

    def test_can_update_group_info(self):
        # Update info
        result = self.client.execute("""mutation { updateGroup(
            id: "1" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name slug description } user { username email name } } }""")

        # The new group info is returned
        self.assertEqual(result["data"]["updateGroup"]["group"], {
            "name": "The Good Guys", "description": "Not so bad", "slug": "good"
        })
        self.assertEqual(result["data"]["updateGroup"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })

        # The group has updated
        group = Group.objects.get(id=1)
        self.assertEqual(group.name, "The Good Guys")
        self.assertEqual(group.slug, "good")
        self.assertEqual(group.description, "Not so bad")
    

    def test_cant_edit_group_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error("""mutation { updateGroup(
            id: "20" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name description } } }""", message="Does not exist")

        # Not an admin
        self.check_query_error("""mutation { updateGroup(
            id: "2" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name description } } }""", message="Not an admin")
    

    def test_cant_edit_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateGroup(
            id: "2" name: "The Good Guys" description: "Not so bad" slug: "good" 
        ) { group { name description } } }""", message="Not authorized")



class GroupDeletingTests(TokenFunctionaltest):

    def test_can_delete_group(self):
        # Delete group
        result = self.client.execute(
            """mutation { deleteGroup(id: "1") {
                success user { username email name }
            } }"""
        )

        # The group is gone
        self.assertTrue(result["data"]["deleteGroup"]["success"])
        self.assertFalse(Group.objects.filter(id=1).count())
        self.assertEqual(result["data"]["deleteGroup"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })
    

    def test_cant_delete_group_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error(
            """mutation { deleteGroup(id: "20") { success } }""",
            message="Does not exist"
        )

        # Not an admin
        self.check_query_error(
            """mutation { deleteGroup(id: "2") { success } }""",
            message="Not an admin"
        )
    

    def test_cant_delete_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteGroup(id: "1") { success } }""",
            message="Not authorized"
        )



class GroupInvitingTests(TokenFunctionaltest):

    def  test_can_invite_user(self):
        # Sends invitation
        result = self.client.execute("""mutation {
            inviteUserToGroup(user: "5" group: "1") { invitation {
                user { username } group { name }
            } }
        }""")

        # Invitation is sent
        self.assertEqual(result["data"]["inviteUserToGroup"]["invitation"], {
            "user": {"username": "juliette"}, "group": {"name": "Shephard Lab"}
        })
        self.assertEqual(
            User.objects.get(id=5).group_invitations.first().group.name, "Shephard Lab"
        )
    

    def test_invitation_must_be_appropriate(self):
        # Must be admin of group
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "5" group: "2") { invitation {
                user { username } group { name }
            } }
        }""", message="Not an admin")

        # Group must exist
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "5" group: "20") { invitation {
                user { username } group { name }
            } }
        }""", message="Does not exist")

        # User must exist
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "50" group: "1") { invitation {
                user { username } group { name }
            } }
        }""", message="Does not exist")

        # User mustn't be member already
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "2" group: "1") { invitation {
                user { username } group { name }
            } }
        }""", message="Already a member")

        # User mustn't be invited already
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "6" group: "1") { invitation {
                user { username } group { name }
            } }
        }""", message="Already invited")


    def test_must_be_logged_in_to_send_invitation(self):
        # Must be logged in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "5" group: "1") { invitation {
                user { username } group { name }
            } }
        }""", message="Not authorized")



class GroupInvitationDeletingTests(TokenFunctionaltest):

    def test_can_delete_invitation(self):
        # Delete invitation as invitee
        result = self.client.execute(
            """mutation { deleteGroupInvitation(id: "2") {
                success user { username email name }
            } }"""
        )

        # The invitation is gone
        self.assertTrue(result["data"]["deleteGroupInvitation"]["success"])
        self.assertFalse(GroupInvitation.objects.filter(id=2).count())
        self.assertEqual(GroupInvitation.objects.count(), 1)
        self.assertEqual(result["data"]["deleteGroupInvitation"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })

        # Delete invitation as admin
        result = self.client.execute(
            """mutation { deleteGroupInvitation(id: "1") { success user { username email name } } }"""
        )
        
        # The invitation is gone
        self.assertTrue(result["data"]["deleteGroupInvitation"]["success"])
        self.assertFalse(GroupInvitation.objects.filter(id=1).count())
        self.assertEqual(GroupInvitation.objects.count(), 0)
        self.assertEqual(result["data"]["deleteGroupInvitation"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })
    

    def test_cant_delete_invitation_if_not_appropriate(self):
        # Group invitation doesn't exist
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "3") { success } }""",
            message="Does not exist"
        )

        # Not an admin or invitee
        invitation = GroupInvitation.objects.create(
            user=User.objects.get(username="boone"),
            group=Group.objects.get(name="The Others"),
            id=4
        )
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "4") { success } }""",
            message="Does not exist"
        )
    

    def test_cant_delete_invitation_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "1") { success } }""",
            message="Not authorized"
        ) 



class GroupAdminRevokeTests(TokenFunctionaltest):

    def test_can_revoke_admin(self):
        # Revoke access
        Group.objects.get(name="The Others").admins.add(User.objects.get(username="jack"))
        result = self.client.execute(
            """mutation { revokeGroupAdmin(group: "2", user: "4") { 
                group { admins { username } }
                user { username email name }
             } }"""
        )

        # User is no longer admin
        self.assertEqual(result["data"]["revokeGroupAdmin"]["group"], {"admins": [
            {"username": "jack"}
        ]})
        self.assertFalse(User.objects.get(username="ben").admin_groups.count())
        self.assertEqual(result["data"]["revokeGroupAdmin"]["user"], {
            "username": "ben", "email": "ben@gmail.com", "name": "Ben Linus"
        })
    

    def test_cant_revoke_admin_if_not_appropriate(self):
        # Not an admin of group
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "2", user: "4") { group { name } } }""",
            message="Not an admin"
        )

        Group.objects.get(name="The Others").admins.add(User.objects.get(username="jack"))
        # Group doesn't exist
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "20", user: "4") { group { name } } }""",
            message="Does not exist"
        )

        # User doesn't exist
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "2", user: "40") { group { name } } }""",
            message="Does not exist"
        )

        # User isn't an admin
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "2", user: "5") { group { name } } }""",
            message="Not an admin"
        )

        # User is only admin
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "1") { group { name } } }""",
            message="only admin"
        )

        
    def test_cant_revoke_admin_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "2", user: "4") { group { name } } }""",
            message="Not authorized"
        )



class GroupAdminAddTests(TokenFunctionaltest):

    def test_can_make_admin(self):
        # Make admin
        result = self.client.execute(
            """mutation { makeGroupAdmin(group: "1", user: "3") { 
                group { admins { username } }
                user { username email name }
             } }"""
        )

        # User is now admin
        self.assertEqual(result["data"]["makeGroupAdmin"]["group"], {"admins": [
            {"username": "jack"}, {"username": "shannon"}
        ]})
        self.assertTrue(User.objects.get(username="shannon").admin_groups.count())
        self.assertEqual(result["data"]["makeGroupAdmin"]["user"], {
            "username": "shannon", "email": "shannon@gmail.com", "name": "Shannon Rutherford"
        })
    

    def test_cant_make_admin_if_not_appropriate(self):
        # Not an admin of group
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "2", user: "5") { group { name } } }""",
            message="Not an admin"
        )

        # Group doesn't exist
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "20", user: "3") { group { name } } }""",
            message="Does not exist"
        )

        # User doesn't exist
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "30") { group { name } } }""",
            message="Does not exist"
        )

        # User isn't a member
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "5") { group { name } } }""",
            message="Not a member"
        )

        # User is already an admin
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "1") { group { name } } }""",
            message="Already an admin"
        )

        
    def test_cant_make_admin_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "3") { group { name } } }""",
            message="Not authorized"
        )



class UserRemovalFromGroupTests(TokenFunctionaltest):

    def test_can_remove_user(self):
        # Remove user
        result = self.client.execute(
            """mutation { removeUserFromGroup(group: "1", user: "3") { 
                group { users { username } }
             } }"""
        )

        # User is no longer in group
        self.assertEqual(result["data"]["removeUserFromGroup"]["group"], {"users": [
            {"username": "jack"}, {"username": "boone"}
        ]})
        self.assertFalse(User.objects.get(username="shannon").groups.count())
    

    def test_removing_user_removed_admin_status(self):
        # Two admins to start with
        group = Group.objects.get(name="Shephard Lab")
        group.admins.add(User.objects.get(username="boone"))
        result = self.client.execute("""{ group(slug: "shephard_lab") {
            name slug users { username } admins { username }
        } }""")
        self.assertEqual(result["data"]["group"], {
            "name": "Shephard Lab", "slug": "shephard_lab",
            "users": [
                {"username": "jack"}, {"username": "boone"},
                {"username": "shannon"},
            ],
            "admins": [{"username": "jack"}, {"username": "boone"}],
        })

        # Removing a user revokes their admin status
        result = self.client.execute(
            """mutation { removeUserFromGroup(group: "1", user: "2") { 
                group { name slug users { username } admins { username } }
             } }"""
        )
        self.assertEqual(result["data"]["removeUserFromGroup"]["group"], {
            "name": "Shephard Lab", "slug": "shephard_lab",
            "users": [
                {"username": "jack"}, {"username": "shannon"},
            ],
            "admins": [{"username": "jack"}],
        })
    

    def test_cant_remove_user_if_not_appropriate(self):
        # Not an admin of group
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "2", user: "5") { group { name } } }""",
            message="Not an admin"
        )

        # Group doesn't exist
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "20", user: "4") { group { name } } }""",
            message="Does not exist"
        )

        # User doesn't exist
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "40") { group { name } } }""",
            message="Does not exist"
        )

        # User isn't in group
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "5") { group { name } } }""",
            message="Not in group"
        )

        
    def test_cant_remove_user_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "4") { group { name } } }""",
            message="Not authorized"
        )



class UserLeavingGroupTests(TokenFunctionaltest):

    def test_can_leave_group(self):
        # Leave group
        result = self.client.execute(
            """mutation { leaveGroup(id: "2") { 
                group { users { username } }
                user { username email name }
             } }"""
        )

        # User is no longer in group
        self.assertEqual(result["data"]["leaveGroup"]["group"], {"users": [
            {"username": "ben"}, {"username": "juliette"}, {"username": "ethan"}
        ]})
        self.assertEqual(User.objects.get(username="jack").groups.count(), 1)
        self.assertEqual(result["data"]["leaveGroup"]["user"], {
            "username": "jack", "email": "jack@gmail.com", "name": "Jack Shephard"
        })
    

    def test_cant_leave_group_if_not_appropriate(self):
        Group.objects.get(name="The Others").users.remove(User.objects.get(username="jack"))
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
        self.check_query_error(
            """mutation { leaveGroup(id: "1") { group { name } } }""",
            message="no admins"
        )


    def test_cant_leave_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { leaveGroup(id: "2") { group { name } } }""",
            message="Not authorized"
        )