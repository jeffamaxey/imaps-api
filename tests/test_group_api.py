from core.models import *
from .base import FunctionalTest

class GroupApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        group = Group.objects.create(
            name="The Group", slug="the-group", description="The group's page."
        )
        group.users.add(User.objects.create(username="adam", email="adam@gmail.com", created=1))
        group.users.add(User.objects.create(username="sarah", email="sarah@gmail.com", created=2))
        group.users.add(User.objects.create(username="john", email="john@gmail.com", created=3))
        group.admins.add(User.objects.get(username="john"))
        User.objects.create(username="lily", created=4)
        group.collections.add(Collection.objects.create(name="C1", private=False))
        group.collections.add(Collection.objects.create(name="C2", private=False))
        group.collections.add(Collection.objects.create(name="C3", private=True))
        Collection.objects.create(name="C4", private=False)
        GroupInvitation.objects.create(group=group, user=User.objects.get(username="lily"))



class GroupQueryTests(GroupApiTests):

    def test_can_get_group(self):
        # Get group
        result = self.client.execute("""{ group(slug: "the-group") {
            name slug description
            users { username } admins { username } collections { name }
            groupInvitations { user { username } }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["group"], {
            "name": "The Group", "slug": "the-group", "description": "The group's page.",
            "users": [{"username": "adam"}, {"username": "sarah"}, {"username": "john"}],
            "admins": [{"username": "john"}],
            "collections": [{"name": "C1"}, {"name": "C2"}],
            "groupInvitations": None
        })
    

    def test_can_get_group_as_member(self):
        # Log in as non-admin member
        self.client.headers["Authorization"] = f"Bearer {User.objects.get(username='adam').make_access_jwt()}"

        # Get group
        result = self.client.execute("""{ group(slug: "the-group") {
            name slug description
            users { username } admins { username } collections { name }
            groupInvitations { user { username } }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["group"], {
            "name": "The Group", "slug": "the-group", "description": "The group's page.",
            "users": [{"username": "adam"}, {"username": "sarah"}, {"username": "john"}],
            "admins": [{"username": "john"}],
            "collections": [{"name": "C1"}, {"name": "C2"}],
            "groupInvitations": None
        })
    

    def test_can_get_group_as_admin(self):
        # Log in as non-admin member
        self.client.headers["Authorization"] = f"Bearer {User.objects.get(username='john').make_access_jwt()}"

        # Get group
        result = self.client.execute("""{ group(slug: "the-group") {
            name slug description
            users { username } admins { username } collections { name }
            groupInvitations { user { username } }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["group"], {
            "name": "The Group", "slug": "the-group", "description": "The group's page.",
            "users": [{"username": "adam"}, {"username": "sarah"}, {"username": "john"}],
            "admins": [{"username": "john"}],
            "collections": [{"name": "C1"}, {"name": "C2"}],
            "groupInvitations": [{"user": {"username": "lily"}}]
        })
    

    def test_invalid_group(self):
        # Slug does not match
        self.check_query_error("""{ group(slug: "xxxxx") {
            id name
        } }""", "not exist")
