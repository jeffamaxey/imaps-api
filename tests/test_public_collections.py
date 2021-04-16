from core.models import *
from .base import FunctionalTest

class PublicCollectionApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
        )
        Collection.objects.create(name="C1", private=True)
        Collection.objects.create(name="C2", private=False)
        CollectionUserLink.objects.create(collection=Collection.objects.create(
            name="C3", private=True
        ), user=self.user, is_owner=True)
        CollectionUserLink.objects.create(collection=Collection.objects.create(
            name="C4", private=False
        ), user=self.user, is_owner=True)
        CollectionUserLink.objects.create(collection=Collection.objects.create(
            name="C5", private=True
        ), user=self.user)
        group = Group.objects.create(name="G1", slug="g1")
        group.users.add(self.user)
        CollectionGroupLink.objects.create(collection=Collection.objects.create(
            name="C6", private=True
        ), group=group)
        CollectionGroupLink.objects.create(collection=Collection.objects.create(
            name="C7", private=False
        ), group=Group.objects.create(name="G2", slug="g2"))
        Sample.objects.create(collection=Collection.objects.get(name="C4"))
        Sample.objects.create(collection=Collection.objects.get(name="C4"))
        Execution.objects.create(collection=Collection.objects.get(name="C4"))
        Execution.objects.create(collection=Collection.objects.get(name="C4"))
        Execution.objects.create(collection=Collection.objects.get(name="C4"))



class UserCollectionsQueryTests(PublicCollectionApiTests):    

    def test_can_get_public_collections(self):
        self.client.headers["Authorization"] = f"Bearer {self.user.make_access_jwt()}"
        result = self.client.execute("""{ publicCollectionCount publicCollections { edges { node {
            name private sampleCount executionCount
            groups { slug } owners { username }
        } } } }""")
        self.assertEqual(result["data"]["publicCollections"]["edges"], [
            {"node": {"name": "C2", "private": False, "sampleCount": 0, "executionCount": 0, "groups": [], "owners": []}},
            {"node": {"name": "C4", "private": False, "sampleCount": 2, "executionCount": 3, "groups": [], "owners": [{"username": "adam"}]}},
            {"node": {"name": "C7", "private": False, "sampleCount": 0, "executionCount": 0, "groups": [{"slug": "g2"}], "owners": []}}
        ])
        self.assertEqual(result["data"]["publicCollectionCount"], 3)