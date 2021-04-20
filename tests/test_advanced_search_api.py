from core.models import *
from .base import FunctionalTest

class CollectionSearchTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        Collection.objects.create(name="C_xyz_1", private=False, id=1, created=1)
        Collection.objects.create(name="C_xy_1", private=False, id=2)
        CollectionUserLink.objects.create(collection=Collection.objects.create(name="C_xyz_2", private=True, id=3), user=self.user, permission=4)
        self.user.collections.add(Collection.objects.create(name="C_xy_2", private=True, id=4))
        Collection.objects.create(name="C_xyz_3", private=True, id=5)
        Collection.objects.create(name="C_4", description="aaxYzbb", private=False, id=6)
        self.user.collections.add(Collection.objects.create(name="C_5", description=".xyz", private=True, id=7))


    def test_can_search_collections(self):
        result = self.client.execute("""{
            searchCollections(query: "xyz") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchCollections"]["edges"], [
            {"node": {"name": "C_xyz_2"}}, {"node": {"name": "C_xyz_1"}}
        ])

    
    def test_can_search_collections_filtered(self):
        # Owner
        result = self.client.execute("""{
            searchCollections(query: "xyz" owner: "adam") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchCollections"]["edges"], [
            {"node": {"name": "C_xyz_2"}}
        ])

        # Creation date
        result = self.client.execute("""{
            searchCollections(query: "xyz" created: "year") { edges { node { name } } }
        }""")

        self.assertEqual(result["data"]["searchCollections"]["edges"], [
            {"node": {"name": "C_xyz_2"}}
        ])



class SampleSearchTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        CollectionUserLink.objects.create(collection=Collection.objects.create(name="C_xyz_2", private=True, id=3), user=self.user, permission=4)
        Sample.objects.create(name="S_xyz_1", organism="sapiens", private=False, id=1, created=1)
        Sample.objects.create(name="S_xy_1", private=False, id=2)
        Sample.objects.create(name="S_xy_2", organism="Homo xyz", private=False, id=3)
        Sample.objects.create(name="S_xy_3", organism="Homo", private=False, id=4)
        Sample.objects.create(name="S_xyz_4", private=True, id=5, collection=self.user.collections.first())


    def test_can_search_samples(self):
        result = self.client.execute("""{
            searchSamples(query: "xyz") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchSamples"]["edges"], [
            {"node": {"name": "S_xyz_4"}}, {"node": {"name": "S_xyz_1"}}
        ])

    
    def test_can_search_samples_filtered(self):
        # Species
        result = self.client.execute("""{
            searchSamples(query: "xyz" organism: "sap") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchSamples"]["edges"], [
            {"node": {"name": "S_xyz_1"}}
        ])

        # Owner
        result = self.client.execute("""{
            searchSamples(query: "xyz" owner: "adam") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchSamples"]["edges"], [
            {"node": {"name": "S_xyz_4"}}
        ])

        # Creation date
        result = self.client.execute("""{
            searchSamples(query: "xyz" created: "year") { edges { node { name } } }
        }""")

        self.assertEqual(result["data"]["searchSamples"]["edges"], [
            {"node": {"name": "S_xyz_4"}}
        ])



class ExecutionSearchTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        CollectionUserLink.objects.create(collection=Collection.objects.create(name="C_xyz_2", private=True, id=3), user=self.user, permission=4)
        Execution.objects.create(name="E_xyz_1", command=Command.objects.create(name="Paraclu"), private=False, id=1, created=1)
        Execution.objects.create(name="E_xy_1", private=False, id=2)
        ExecutionUserLink.objects.create(
            execution=Execution.objects.create(name="E_xyz_4", private=True, id=5),
            user=self.user,
            permission=4
        )


    def test_can_search_executions(self):
        result = self.client.execute("""{
            searchExecutions(query: "xyz") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchExecutions"]["edges"], [
            {"node": {"name": "E_xyz_1"}}, {"node": {"name": "E_xyz_4"}}
        ])

    
    def test_can_search_executions_filtered(self):
        # Command
        result = self.client.execute("""{
            searchExecutions(query: "xyz" command: "par") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchExecutions"]["edges"], [
            {"node": {"name": "E_xyz_1"}}
        ])

        # Owner
        result = self.client.execute("""{
            searchExecutions(query: "xyz" owner: "adam") { edges { node { name } } }
        }""")
        self.assertEqual(result["data"]["searchExecutions"]["edges"], [
            {"node": {"name": "E_xyz_4"}}
        ])

        # Creation date
        result = self.client.execute("""{
            searchExecutions(query: "xyz" created: "year") { edges { node { name } } }
        }""")

        self.assertEqual(result["data"]["searchExecutions"]["edges"], [
            {"node": {"name": "E_xyz_4"}}
        ])