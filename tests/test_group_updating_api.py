from core.models import *
from .base import FunctionalTest

class GroupUpdatingApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            id=1, username="adam", email="adam@crick.ac.uk", name="Adam A",
            last_login=1617712117, created=1607712117, company="The Crick",
            department="MolBio", lab="The Smith Lab", job_title="Researcher",
        )
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.group.admins.add(self.user)
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"



class MultipleUsersTests(FunctionalTest):

    def test_can_get_multiple_users(self):
        User.objects.create(
            username="jo", email="jo@crick.ac.uk", name="Jo J",
            last_login=1627712117, created=1607912117, company="The Crick",
            department="MolBio", lab="The Jones Lab", job_title="PI",
        )

        result = self.client.execute("""{ users {
            username email name lastLogin created company department lab jobTitle
        } }""")
        self.assertEqual(result["data"]["users"], [{
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A",
            "lastLogin": 1617712117, "created": 1607712117, "company": "The Crick",
            "department": "MolBio", "lab": "The Smith Lab", "jobTitle": "Researcher",
        }, {
            "username": "jo", "email": "", "name": "Jo J",
            "lastLogin": None, "created": 1607912117, "company": "The Crick",
            "department": "MolBio", "lab": "The Jones Lab", "jobTitle": "PI",
        }])



class GroupUpdatingTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)


    def test_can_update_group_info(self):
        # Update info
        result = self.client.execute("""mutation { updateGroup(
            id: "1" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name slug description } user { username name } } }""")

        # The new group info is returned
        self.assertEqual(result["data"]["updateGroup"]["group"], {
            "name": "The Good Guys", "description": "Not so bad", "slug": "good"
        })
        self.assertEqual(result["data"]["updateGroup"]["user"], {
            "username": "adam", "name": "Adam A"
        })

        # The group has updated
        group = Group.objects.get(id=1)
        self.assertEqual(group.name, "The Good Guys")
        self.assertEqual(group.slug, "good")
        self.assertEqual(group.description, "Not so bad")
    

    def test_cant_edit_group_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error("""mutation { updateGroup(
            id: "2" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name description } } }""", message="Does not exist")

        # Not an admin
        self.link.permission = 2
        self.link.save()
        self.check_query_error("""mutation { updateGroup(
            id: "1" name: "The Good Guys" description: "Not so bad" slug: "good"
        ) { group { name description } } }""", message="Not an admin")
    

    def test_cant_edit_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateGroup(
            id: "1" name: "The Good Guys" description: "Not so bad" slug: "good" 
        ) { group { name description } } }""", message="Not authorized")



class GroupAdminAddTests(GroupUpdatingApiTests):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)
        self.user2 = User.objects.create(id=2, username="charles", email="charles@gmail.com")
        self.link2 = UserGroupLink.objects.create(user=self.user2, group=self.group, permission=2)

    def test_can_make_admin(self):
        # Make admin
        result = self.client.execute(
            """mutation { makeGroupAdmin(group: "1", user: "2") { 
                group { admins { username } }
                user { username email name }
             } }"""
        )

        # User is now admin
        self.assertEqual(result["data"]["makeGroupAdmin"]["group"], {"admins": [
            {"username": "adam"}, {"username": "charles"}
        ]})
        self.assertTrue(User.objects.get(username="charles").admin_groups.count())
        self.assertEqual(result["data"]["makeGroupAdmin"]["user"], {
            "username": "charles", "email": "", "name": ""
        })
    

    def test_cant_make_admin_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "10", user: "2") { group { name } } }""",
            message="Does not exist"
        )

        # Not an admin of group
        self.link.permission = 2
        self.link.save()
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "2") { group { name } } }""",
            message="Not an admin"
        )

        # User doesn't exist
        self.link.permission = 3
        self.link.save()
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "30") { group { name } } }""",
            message="Does not exist"
        )

        # User isn't a member
        self.link2.permission = 1
        self.link2.save()
        self.check_query_error(
            """mutation { makeGroupAdmin(group: "1", user: "2") { group { name } } }""",
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



class GroupAdminRevokeTests(GroupUpdatingApiTests):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)
        self.user2 = User.objects.create(id=2, username="charles", email="charles@gmail.com")
        self.link2 = UserGroupLink.objects.create(user=self.user2, group=self.group, permission=3)


    def test_can_revoke_admin(self):
        # Revoke access
        result = self.client.execute(
            """mutation { revokeGroupAdmin(group: "1", user: "1") { 
                group { admins { username } }
                user { username email name }
             } }"""
        )

        # User is no longer admin
        self.assertEqual(result["data"]["revokeGroupAdmin"]["group"], {"admins": [
            {"username": "charles"}
        ]})
        self.assertFalse(User.objects.get(username="adam").admin_groups.count())
        self.assertEqual(result["data"]["revokeGroupAdmin"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_revoke_admin_if_not_appropriate(self):
        # User isn't an admin
        self.link2.permission = 2
        self.link2.save()
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "2") { group { name } } }""",
            message="Not an admin"
        )
        self.link2.permission = 3
        self.link2.save()

        # Group doesn't exist
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "20", user: "2") { group { name } } }""",
            message="Does not exist"
        )

        # User doesn't exist
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "40") { group { name } } }""",
            message="Does not exist"
        )

        # User is only admin
        self.link2.permission = 2
        self.link2.save()
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "1") { group { name } } }""",
            message="only admin"
        )

        # Logged in user isn't an admin
        self.client.headers["Authorization"] = f"Bearer {self.user2.make_access_jwt()}"
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "1") { group { name } } }""",
            message="Not an admin"
        )

        
    def test_cant_revoke_admin_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { revokeGroupAdmin(group: "1", user: "1") { group { name } } }""",
            message="Not authorized"
        )




class UserRemovalFromGroupTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)
        self.user2 = User.objects.create(id=2, username="charles", email="charles@gmail.com")
        self.link2 = UserGroupLink.objects.create(user=self.user2, group=self.group, permission=2)


    def test_can_remove_user(self):
        # Remove user
        self.group.users.add(self.user2)
        result = self.client.execute(
            """mutation { removeUserFromGroup(group: "1", user: "2") { 
                group { members { username } }
             } }"""
        )

        # User is no longer in group
        self.assertEqual(result["data"]["removeUserFromGroup"]["group"], {"members": [{"username": "adam"}]})
        self.assertFalse(User.objects.get(username="charles").groups.count())
        

    def test_cant_remove_user_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "20", user: "2") { group { name } } }""",
            message="Does not exist"
        )

        # User does not exist
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "20") { group { name } } }""",
            message="Does not exist"
        )

        # User is not in group
        self.link2.permission = 1
        self.link2.save()
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "2") { group { name } } }""",
            message="Not in group"
        )

        # Not an admin of group
        self.link2.permission = 2
        self.link2.save()
        self.client.headers["Authorization"] = f"Bearer {self.user2.make_access_jwt()}"
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "2") { group { name } } }""",
            message="Not an admin"
        )

        
    def test_cant_remove_user_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { removeUserFromGroup(group: "1", user: "4") { group { name } } }""",
            message="Not authorized"
        )



class GroupInvitingTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)
        self.user2 = User.objects.create(id=2, username="charles", email="charles@gmail.com")


    def  test_can_invite_user(self):

        # Sends invitation
        result = self.client.execute("""mutation {
            inviteUserToGroup(user: "2" group: "1") {
                user { username } group { name }
            }
        }""")

        # Invitation is sent
        self.assertEqual(result["data"]["inviteUserToGroup"], {
            "user": {"username": "charles"}, "group": {"name": "The Group"}
        })
        self.assertEqual(
            User.objects.get(id=2).invitations.first().name, "The Group"
        )
    

    def test_invitation_must_be_appropriate(self):
        # Group must exist
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "2" group: "20") { 
                user { username } group { name }
            } 
        }""", message="Does not exist")

        # User must exist
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "50" group: "1") { 
                user { username } group { name }
            } 
        }""", message="Does not exist")

        # User must not be member already
        link = UserGroupLink.objects.create(user=self.user2, group=self.group, permission=2)
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "2" group: "1") { 
                user { username } group { name }
            } 
        }""", message="Already connected")

        # User must not be invited already
        link.permission = 1
        link.save()
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "2" group: "1") { 
                user { username } group { name }
            } 
        }""", message="Already connected")

        # Must be admin of group
        self.client.headers["Authorization"] = f"Bearer {self.user2.make_access_jwt()}"
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "2" group: "1") {
                user { username } group { name }
            }
        }""", message="Not an admin")


    def test_must_be_logged_in_to_send_invitation(self):
        # Must be logged in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            inviteUserToGroup(user: "5" group: "1") {
                user { username } group { name }
            }
        }""", message="Not authorized")



class GroupInvitationProcessingTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)
        self.user2 = User.objects.create(id=2, username="charles", email="charles@gmail.com")
        self.link2 = UserGroupLink.objects.create(user=self.user2, group=self.group, permission=1)


    def test_can_delete_invitation_as_admin(self):
        # Delete invitation as admin
        result = self.client.execute(
            """mutation { processGroupInvitation(group: "1" user: "2" accept: false) {
                success user { username email name } }
            }"""
        )
        
        # The invitation is gone
        self.assertTrue(result["data"]["processGroupInvitation"]["success"])
        self.assertEqual(UserGroupLink.objects.count(), 1)
        self.assertEqual(result["data"]["processGroupInvitation"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_delete_invitation_if_not_appropriate(self):
        # Group invitation doesn't exist
        self.check_query_error(
            """mutation { processGroupInvitation(group: "1" user: "20" accept: false) { success } }""",
            message="Does not exist"
        )

        # Not an admin
        self.link.permission = 2
        self.link.save()
        self.check_query_error(
            """mutation { processGroupInvitation(group: "1" user: "20" accept: false) { success } }""",
            message="Does not exist"
        )

        # Can't accept for user
        self.link.permission = 3
        self.link.save()
        self.check_query_error(
            """mutation { processGroupInvitation(group: "1" user: "2" accept: true) { success } }""",
            message="User must accept"
        )
    

    def test_cant_delete_invitation_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { processGroupInvitation(group: "1" user: "2" accept: false) { success } }""",
            message="Not authorized"
        ) 



class GroupDeletingTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.group = Group.objects.create(
            id=1, name="The Group", slug="the-group", description="Our group page"
        )
        self.link = UserGroupLink.objects.create(user=self.user, group=self.group, permission=3)


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
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_delete_group_if_not_appropriate(self):
        # Group doesn't exist
        self.check_query_error(
            """mutation { deleteGroup(id: "20") { success } }""",
            message="Does not exist"
        )

        # Not an admin
        self.link.permission = 2
        self.link.save()
        self.check_query_error(
            """mutation { deleteGroup(id: "1") { success } }""",
            message="Not an admin"
        )
    

    def test_cant_delete_group_when_not_logged_in(self):
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteGroup(id: "1") { success } }""",
            message="Not authorized"
        )