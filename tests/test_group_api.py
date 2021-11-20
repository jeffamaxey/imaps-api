from django.test.testcases import TestCase
from core.models import User, Group, UserGroupLink
from analysis.models import Collection
from .base import FunctionalTest

class GroupQueryTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        group = Group.objects.create(
            name="The Group", slug="the-group", description="The group's page."
        )
        self.user.created = 1
        self.user.save()
        UserGroupLink.objects.create(user=self.user, group=group, permission=2)
        UserGroupLink.objects.create(
            user=User.objects.create(username="sarah", email="sarah@gmail.com", created=2),
            group=group, permission=2
        )
        UserGroupLink.objects.create(
            user=User.objects.create(username="john", email="john@gmail.com", created=3),
            group=group, permission=3
        )
        UserGroupLink.objects.create(
            user=User.objects.create(username="lily", created=4), group=group, permission=1
        )

        group.collections.add(Collection.objects.create(name="C1", private=False))
        group.collections.add(Collection.objects.create(name="C2", private=False))
        group.collections.add(Collection.objects.create(name="C3", private=True))
        Collection.objects.create(name="C4", private=False)


    def test_can_get_group(self):
        # Get group
        result = self.client.execute("""{ group(slug: "the-group") {
            name slug description userCount
            members { username } admins { username } publicCollections { name }
            invitees { username }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["group"], {
            "name": "The Group", "slug": "the-group", "description": "The group's page.",
            "userCount": 3,
            "members": [{"username": "adam"}, {"username": "sarah"}, {"username": "john"}],
            "admins": [{"username": "john"}],
            "publicCollections": [{"name": "C1"}, {"name": "C2"}],
            "invitees": [{"username": "lily"}]
        })
    

    def test_invalid_group(self):
        # Slug does not match
        self.check_query_error("""{ group(slug: "xxxxx") {
            id name
        } }""", "not exist")
