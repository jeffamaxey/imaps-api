from core.models import *
from .base import FunctionalTest

class UserApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
            last_login=1617712117, created=1607712117, company="The Crick",
            department="MolBio", lab="The Smith Lab", job_title="Researcher",
        )
        user.groups.add(Group.objects.create(name="Group 1", slug="group1"))
        user.groups.add(Group.objects.create(name="Group 2", slug="group2"))
        GroupInvitation.objects.create(
            group=Group.objects.create(name="Group 3", slug="group3"),
            user=user
        )
        c1 = Collection.objects.create(name="Collection 1", private=False)
        c2 = Collection.objects.create(name="Collection 2", private=False)
        c3 = Collection.objects.create(name="Collection 3", private=True)
        c4 = Collection.objects.create(name="Collection 4", private=False)
        c5 = Collection.objects.create(name="Collection 5", private=False)
        CollectionUserLink.objects.create(collection=c1, user=user, is_owner=True)
        CollectionUserLink.objects.create(collection=c2, user=user, is_owner=True)
        CollectionUserLink.objects.create(collection=c3, user=user, is_owner=True)
        CollectionUserLink.objects.create(collection=c4, user=user, is_owner=False)




class PublicUserTests(UserApiTests):

    def test_can_get_user_information(self):
        # Get user
        result = self.client.execute("""{ user(username: "adam") {
            username email name lastLogin created jobTitle lab company
            department collections { name } groups { name } groupInvitations { id }
        } }""")

        # Everything is correct
        self.assertEqual(result["data"]["user"], {
            "username": "adam", "email": "",
            "name": "Adam A", "lastLogin": None, "created": 1607712117,
            "jobTitle": "Researcher", "lab": "The Smith Lab", "company": "The Crick",
            "department": "MolBio", "groupInvitations": None,
            "groups": [{"name": "Group 1"}, {"name": "Group 2"}],
            "collections": [{"name": "Collection 1"}, {"name": "Collection 2"}],
        })
    

    def test_invalid_user_requests(self):
        # Incorrect username
        self.check_query_error("""{ user(username: "smoke") {
            name username
        } }""", message="Does not exist")
