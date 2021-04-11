import requests
from core.models import *
from .base import FunctionalTest

class BaseApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
            last_login=1617712117, created=1607712117, company="The Crick",
            department="MolBio", lab="The Smith Lab", job_title="Researcher",
        )
        User.objects.create(
            username="sally", email="sally@crick.ac.uk", name="Sally S"
        )
        self.user.admin_groups.add(Group.objects.create(
            name="Smith Lab", slug="smithlab", description="lab of John Smith"
        ))
        self.user.groups.add(Group.objects.create(
            name="Jones Lab", slug="joneslab", description="lab of Sarah Jones"
        ))
        self.user.groups.add(Group.objects.create(
            name="Barker Lab", slug="barkerlab", description="lab of Billy Barker"
        ))
        GroupInvitation.objects.create(
            id=1, user=self.user, group=Group.objects.create(
                name="Davies Lab", slug="davies", description="lab of Dora Davies"
            )
        )



class AccessTokenTests(BaseApiTests):

    def test_can_get_access_token(self):
        # Send query with cookie
        original_refresh_token = self.user.make_refresh_jwt()
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token",
            value=original_refresh_token
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        result = self.client.execute("{ accessToken }")

        # An access token has been returned
        access_token = result["data"]["accessToken"]
        algorithm, payload, secret = access_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 900, 10)

        # A new HTTP-only cookie has been set with the refresh token
        cookie = self.client.session.cookies._cookies["localhost.local"]["/"]["refresh_token"]
        self.assertIn("HttpOnly", cookie._rest)
        self.assertLess(time.time() - cookie.expires - 31536000, 10)
        refresh_token = cookie.value
        algorithm, payload, secret = refresh_token.split(".")
        payload = json.loads(base64.b64decode(payload + "==="))
        self.assertEqual(payload["sub"], self.user.id)
        self.assertLess(time.time() - payload["iat"], 10)
        self.assertLess(time.time() - payload["expires"] - 31536000, 10)
    

    def test_token_refresh_can_fail(self):
        # No cookies
        self.check_query_error(
            "{ accessToken }", message="No refresh token"
        )
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Refresh token garbled
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token", value="sadafasdf"
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        self.check_query_error(
            "{ accessToken }", message="Refresh token not valid"
        )
        
        # Refresh token expired
        token = jwt.encode({
            "sub": self.user.id, "iat": 1000000000000, "expires": 2000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token", value=token
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        self.check_query_error(
            "{ accessToken }", message="Refresh token not valid"
        )



class LoggedInUserAccess(BaseApiTests):

    def test_can_get_logged_in_user(self):
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        result = self.client.execute("""{ user {
            username email name lastLogin created jobTitle lab company
            department groupInvitations { group { name } }
        } }""")
        self.assertEqual(result["data"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A",
            "lastLogin": 1617712117, "created": 1607712117, "jobTitle": "Researcher",
            "lab": "The Smith Lab", "company": "The Crick", "department": "MolBio",
            "groupInvitations": [{"group": {"name": "Davies Lab"}}]
        })
    

    def test_cant_get_user_if_not_authorized(self):
        # No token
        self.check_query_error("{ user { username } }", "authorized")

        # Garbled token
        self.client.headers["Authorization"] = "Bearer 23424"
        self.check_query_error("{ user { username } }", "authorized")

        # Expired token
        token = jwt.encode({
            "sub": self.user.id, "iat": 1000000000000, "expires": 2000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
        self.client.headers["Authorization"] = token
        self.check_query_error("{ user { username } }", "authorized")



class LogoutTests(BaseApiTests):

    def test_can_logout(self):
        # Start with refresh token
        refresh_token = self.user.make_refresh_jwt()
        cookie_obj = requests.cookies.create_cookie(
            domain="localhost.local", name="refresh_token",
            value=refresh_token
        )
        self.client.session.cookies.set_cookie(cookie_obj)
        self.assertTrue("refresh_token" in self.client.session.cookies)

        # Log out
        result = self.client.execute("mutation { logout { success } }")

        # Cookie gone
        self.assertTrue(result["data"]["logout"]["success"])
        self.assertFalse("refresh_token" in self.client.session.cookies)
    

    def test_logout_works_without_cookie(self):
        # No cookies
        self.assertFalse("refresh_token" in self.client.session.cookies)

        # Log out
        result = self.client.execute("mutation { logout { success } }")

        # Still no cookie
        self.assertTrue(result["data"]["logout"]["success"])
        self.assertFalse("refresh_token" in self.client.session.cookies)



class GroupInvitationDeletingTests(BaseApiTests):

    def test_can_delete_invitation_as_invitee(self):
        # Delete invitation as invitee
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        result = self.client.execute(
            """mutation { deleteGroupInvitation(id: "1") {
                success user { username email name }
            } }"""
        )

        # The invitation is gone
        self.assertTrue(result["data"]["deleteGroupInvitation"]["success"])
        self.assertFalse(GroupInvitation.objects.filter(id=1).count())
        self.assertEqual(GroupInvitation.objects.count(), 0)
        self.assertEqual(result["data"]["deleteGroupInvitation"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_delete_invitation_if_not_appropriate(self):
        # Group invitation does not exist
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "3") { success } }""",
            message="Does not exist"
        )

        # Not the invitee
        invitation = GroupInvitation.objects.create(
            user=User.objects.get(username="sally"),
            group=Group.objects.get(name="Davies Lab"),
            id=2
        )
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "2") { success } }""",
            message="Does not exist"
        )
    

    def test_cant_delete_invitation_when_not_logged_in(self):
        self.check_query_error(
            """mutation { deleteGroupInvitation(id: "1") { success } }""",
            message="Not authorized"
        ) 



class GroupInvitationAcceptanceTests(BaseApiTests):

    def test_can_accept_invitation(self):
        # Accept invitation
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        result = self.client.execute(
            """mutation { acceptGroupInvitation(id: "1") { 
                group { users { username } }
                user { username email name }
             } }"""
        )

        # The invitation is gone
        self.assertEqual(result["data"]["acceptGroupInvitation"]["group"], {"users": [
            {"username": "adam"}
        ]})
        self.assertFalse(GroupInvitation.objects.filter(id=1).count())
        self.assertEqual(GroupInvitation.objects.count(), 0)
        self.assertEqual(result["data"]["acceptGroupInvitation"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_cant_accept_invitation_if_not_appropriate(self):
        # Group invitation does not exist
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        self.check_query_error(
            """mutation { acceptGroupInvitation(id: "2") { group { name } } }""",
            message="Does not exist"
        )

        # Not the invitee
        invitation = GroupInvitation.objects.create(
            user=User.objects.get(username="sally"),
            group=Group.objects.get(name="Davies Lab"),
            id=2
        )
        self.check_query_error(
            """mutation { acceptGroupInvitation(id: "2") { group { name } } }""",
            message="Does not exist"
        )
    

    def test_cant_accept_invitation_when_not_logged_in(self):
        self.check_query_error(
            """mutation { acceptGroupInvitation(id: "1") { group { name } } }""",
            message="Not authorized"
        )



class QuickSearchTests(BaseApiTests):

    def test_need_three_characters(self):
        result = self.client.execute("""{
            quickSearch(query: "") { results { name } }
        }""")
        self.assertIsNone(result["data"]["quickSearch"])

        result = self.client.execute("""{
            quickSearch(query: "X") { results { name } }
        }""")
        self.assertIsNone(result["data"]["quickSearch"])

        result = self.client.execute("""{
            quickSearch(query: "XX") { results { name } }
        }""")
        self.assertIsNone(result["data"]["quickSearch"])
    

    def test_can_return_no_matches(self):
        result = self.client.execute("""{
            quickSearch(query: "XXX") { results { name } }
        }""")
        self.assertEqual(result["data"]["quickSearch"]["results"], [])
    

    def test_can_return_results(self):
        Collection.objects.create(name="C_xyz_1", private=False, id=1)
        Collection.objects.create(name="C_xy_1", private=False, id=2)
        self.user.collections.add(Collection.objects.create(name="C_xyz_2", private=True, id=3))
        self.user.collections.add(Collection.objects.create(name="C_xy_2", private=True, id=4))
        Collection.objects.create(name="C_xyz_3", private=True, id=5)
        Collection.objects.create(name="C_4", description="aaxyzbb", private=False, id=6)
        self.user.collections.add(Collection.objects.create(name="C_5", description=".xyz", private=True, id=7))

        Sample.objects.create(name="S_xyz_1", private=False, id=1)
        Sample.objects.create(name="S_xy_1", private=False, id=2)
        Sample.objects.create(name="S_xy_2", organism="Homo xyz", private=False, id=3)
        Sample.objects.create(name="S_xy_3", organism="Homo", private=False, id=4)
        Sample.objects.create(name="S_xyz_4", private=True, id=5, collection=self.user.collections.first())

        Execution.objects.create(name="E_xyz_1", private=False, id=1)
        Execution.objects.create(name="E_xy_1", private=False, id=2)
        Execution.objects.create(name="E_xyz_4", private=True, id=5, collection=self.user.collections.first())

        Group.objects.create(name="The 123 Group", description="We do xyz", slug="123")
        Group.objects.create(name="The xyz Group", slug="xyz")
        Group.objects.create(name="The abc Group", slug="abc")

        User.objects.create(name="Dr xyz", email="xyz@gmail.com", username="xyz")
        User.objects.create(name="Dr 123", email="123@gmail.com", username="123")


        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        result = self.client.execute("""{
            quickSearch(query: "xyz") { results { name kind pk match matchLoc } }
        }""")

        self.assertEqual(result["data"]["quickSearch"]["results"], [
            {"name": "C_xyz_1", "kind": "Collection", "pk": "1", "match": "", "matchLoc": None},
            {"name": "C_xyz_2", "kind": "Collection", "pk": "3", "match": "", "matchLoc": None},
            {"name": "C_4", "kind": "Collection", "pk": "6", "match": "aaxyzbb", "matchLoc": [2, 5]},
            {"name": "C_5", "kind": "Collection", "pk": "7", "match": ".xyz", "matchLoc": [1, 4]},
            {"name": "S_xyz_1", "kind": "Sample", "pk": "1", "match": "", "matchLoc": None},
            {"name": "S_xyz_4", "kind": "Sample", "pk": "5", "match": "", "matchLoc": None},
            {"name": "S_xy_2", "kind": "Sample", "pk": "3", "match": "Homo xyz", "matchLoc": [5, 8]},
            {"name": "E_xyz_1", "kind": "Execution", "pk": "1", "match": "", "matchLoc": None},
            {"name": "E_xyz_4", "kind": "Execution", "pk": "5", "match": "", "matchLoc": None},
            {"name": "The xyz Group", "kind": "Group", "pk": "xyz", "match": "", "matchLoc": None},
            {"name": "The 123 Group", "kind": "Group", "pk": "123", "match": "We do xyz", "matchLoc": [6, 9]},
            {"name": "Dr xyz", "kind": "User", "pk": "xyz", "match": "", "matchLoc": None},
        ])