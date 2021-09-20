from core.models import User, Group
from samples.models import Collection, Sample, CollectionUserLink, CollectionGroupLink
from execution.models import Execution
from .base import FunctionalTest

class UserCollectionApiTests(FunctionalTest):

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
        ), user=self.user, can_edit=True)
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
        Sample.objects.create(collection=Collection.objects.get(name="C3"))
        Sample.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))



class UserCollectionsQueryTests(UserCollectionApiTests):

    def setUp(self):
        FunctionalTest.setUp(self)
        Collection.objects.create(name="C1", private=True)
        Collection.objects.create(name="C2", private=False)
        CollectionUserLink.objects.create(collection=Collection.objects.create(
            name="C3", private=True
        ), user=self.user, permission=4)
        CollectionUserLink.objects.create(collection=Collection.objects.create(
            name="C4", private=False
        ), user=self.user, permission=2)
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
        Sample.objects.create(collection=Collection.objects.get(name="C3"))
        Sample.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))
        Execution.objects.create(collection=Collection.objects.get(name="C3"))


    def test_no_results_when_logged_out(self):
        del self.client.headers["Authorization"]
        result = self.client.execute("""{ userCollections {
            id name description
        } }""")
        self.assertEqual(result["data"]["userCollections"], [])
    

    def test_can_get_users_collections(self):
        result = self.client.execute("""{ userCollections {
            name private sampleCount executionCount
            groups { slug } owners { username }
        } }""")
        self.assertEqual(result["data"]["userCollections"], [
            {"name": "C3", "private": True, "sampleCount": 2, "executionCount": 3, "groups": [], "owners": [{"username": "adam"}]},
            {"name": "C4", "private": False, "sampleCount": 0, "executionCount": 0, "groups": [], "owners": []},
            {"name": "C5", "private": True, "sampleCount": 0, "executionCount": 0, "groups": [], "owners": []},
            {"name": "C6", "private": True, "sampleCount": 0, "executionCount": 0, "groups": [{"slug": "g1"}], "owners": []}
        ])