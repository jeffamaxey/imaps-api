from core.models import *
from .base import FunctionalTest
class PublicUserTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        UserGroupLink.objects.create(
            user=self.user, group=Group.objects.create(name="Group 1", slug="group1"), permission=2
        )
        UserGroupLink.objects.create(
            user=self.user, group=Group.objects.create(name="Group 2", slug="group2"), permission=2
        )
        c1 = Collection.objects.create(name="Collection 1", private=False)
        c2 = Collection.objects.create(name="Collection 2", private=False)
        c3 = Collection.objects.create(name="Collection 3", private=True)
        c4 = Collection.objects.create(name="Collection 4", private=False)
        c5 = Collection.objects.create(name="Collection 5", private=False)
        CollectionUserLink.objects.create(collection=c1, user=self.user, permission=4)
        CollectionUserLink.objects.create(collection=c2, user=self.user, permission=4)
        CollectionUserLink.objects.create(collection=c3, user=self.user, permission=4)
        CollectionUserLink.objects.create(collection=c4, user=self.user, permission=3)
        del self.client.headers["Authorization"]


    def test_can_get_user_information(self):
        # Get user
        result = self.client.execute("""{ user(username: "adam") {
            username email name lastLogin created jobTitle lab company
            department publicCollections { name } memberships { name }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["user"], {
            "username": "adam", "email": "",
            "name": "Adam A", "lastLogin": None, "created": 1607712117,
            "jobTitle": "Researcher", "lab": "The Smith Lab", "company": "The Crick",
            "department": "MolBio",
            "memberships": [{"name": "Group 1"}, {"name": "Group 2"}],
            "publicCollections": [{"name": "Collection 1"}, {"name": "Collection 2"}],
        })
    

    def test_invalid_user_requests(self):
        # Incorrect username
        self.check_query_error("""{ user(username: "smoke") {
            name username
        } }""", message="Does not exist")
