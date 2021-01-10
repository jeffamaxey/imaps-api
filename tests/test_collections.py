from .base import FunctionalTest, TokenFunctionaltest
from core.models import Collection

class CollectionQueryTests(TokenFunctionaltest):

    def test_can_get_collection(self):
        # Get own collection
        collection = Collection.objects.get(id="1")
        collection.private = True
        collection.save()
        result = self.client.execute("""{ collection(id: "1") {
            name description creationTime private canEdit canExecute
            owner { username } users { username } groups { name }
            papers { title year }
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "name": "Experiment 1", "description": "Initial explorations.",
            "canEdit": True, "canExecute": True,
            "creationTime": 946684800, "private": True, "owner": {"username": "jack"},
            "users": [{"username": "boone"}, {"username": "shannon"}],
            "groups": [], "papers": [{"title": "Paper 1", "year": 2004}]
        })

        # Get collection with user access
        collection = Collection.objects.get(id="2")
        collection.groups.remove(collection.groups.first())
        collection.users.add(self.user)
        collection.save()
        result = self.client.execute("""{ collection(id: "2") {
            name description papers { title } private canEdit canExecute
            owner { username } users { username } groups { name }
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "name": "Experiment 2", "description": "Secret explorations.",
            "canEdit": True, "canExecute": False,
            "private": True, "owner": {"username": "boone"},
            "users": [{"username": "jack"}, {"username": "shannon"}],
            "groups": [], "papers": []
        })

        # Get collection with group access
        collection = Collection.objects.get(id="3")
        collection.users.remove(self.user)
        collection.save()
        result = self.client.execute("""{ collection(id: "3") {
            name description papers { title } private canEdit canExecute
            owner { username } users { username } groups { name }
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "name": "Experiment 3", "description": "Secret explorations.",
            "canEdit": True, "canExecute": False,
            "private": True, "owner": {"username": "shannon"},
            "users": [{"username": "boone"}],
            "groups": [{"name": "Shephard Lab"}], "papers": []
        })

        # Get public collection
        collection = Collection.objects.get(id="5")
        collection.private = False
        collection.save()
        result = self.client.execute("""{ collection(id: "5") {
            name description papers { title } private canEdit canExecute
            owner { username } users { username } groups { name }
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "name": "Experiment 5", "description": "",
            "private": False, "owner": {"username": "juliette"},
            "canEdit": False, "canExecute": False,
            "users": [{"username": "ethan"}],
            "groups": [], "papers": []
        })
    

    def test_cant_get_invalid_collections(self):
        # Incorrect ID
        self.check_query_error("""{ collection(id: "999") {
            name
        } }""", message="Does not exist")

        # Inaccessible collection
        self.check_query_error("""{ collection(id: "5") {
            name
        } }""", message="Does not exist")

        # Private collection when logged out
        del self.client.headers["Authorization"]
        self.check_query_error("""{ collection(id: "2") {
            name
        } }""", message="Does not exist")
    

    def test_can_get_all_collections(self):
        # Any group
        result = self.client.execute("""{
            collections { edges { node { name } } }
            collectionCount
        }""")
        self.assertEqual(result["data"]["collections"], {"edges": [
           {"node": {"name": "Experiment 4"}}, {"node": {"name": "Experiment 1"}}
        ]})
        self.assertEqual(result["data"]["collectionCount"], 2)

    
    def test_can_get_paginated_collections(self):
        Collection.objects.create(name="C3", owner=self.user, private=False, creation_time=1000)
        Collection.objects.create(name="C4", owner=self.user, private=False, creation_time=2000)
        Collection.objects.create(name="C5", owner=self.user, private=False, creation_time=3000)

        result = self.client.execute("""{ collections(first: 3) {
            edges { node { name } }
        } }""")
        self.assertEqual(result["data"]["collections"], {"edges": [
           {"node": {"name": "Experiment 4"}}, {"node": {"name": "Experiment 1"}},
           {"node": {"name": "C5"}}
        ]})

        result = self.client.execute("""{ collections(first: 3, offset: 2) {
            edges { node { name } }
        } }""")
        self.assertEqual(result["data"]["collections"], {"edges": [
           {"node": {"name": "C5"}}, {"node": {"name": "C4"}},
           {"node": {"name": "C3"}}
        ]})
