
from core.models import Group
from .base import FunctionalTest

class GroupCreationTests(FunctionalTest):

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
            "users": [{"username": "adam"}], "admins": [{"username": "adam"}]
        })
        self.assertEqual(result["data"]["createGroup"]["user"], {
            "username": "adam", "email": "adam@crick.ac.uk", "name": "Adam A"
        })
    

    def test_group_creation_validation(self):
        # Name must not be too long
        self.check_query_error("""mutation { createGroup(
            name: \"""" + "." * 51 + """\", description: "The A Team", slug: "others"
        ) { group { name description users { username } admins { username } } } }""",
        message="50 characters")

        # Slug must not be too long
        self.check_query_error("""mutation { createGroup(
            slug: \"""" + "." * 51 + """\", description: "The A Team", name: "others"
        ) { group { name description users { username } admins { username } } } }""",
        message="50 characters")

        # Slug must be unique
        Group.objects.create(name="Others", slug="others")
        self.check_query_error("""mutation { createGroup(
            slug: "others", description: "The A Team", name: "others"
        ) { group { name description users { username } admins { username } } } }""",
        message="already exists")

        # Description must not be too long
        self.check_query_error("""mutation { createGroup(
            description: \"""" + "." * 201 + """\", name: "The A Team", slug: "others2"
        ) { group { name description users { username } admins { username } } } }""",
        message="200 characters")


    def test_must_be_logged_in_to_create_group(self):
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { createGroup(
            name: "A Team", description: "The A Team", slug: "a_team"
        ) { group { name description users { username } admins { username } } } }""",
        message="Not authorized")