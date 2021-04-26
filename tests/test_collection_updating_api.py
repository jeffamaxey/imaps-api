from core.models import *
from .base import FunctionalTest

class CollectionUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        self.collection = Collection.objects.create(
            id=1, name="My Collection", private=True,
            description="Collection desc"
        )
        self.link = CollectionUserLink.objects.create(collection=self.collection, user=self.user, permission=4)
        Paper.objects.create(
            title="Paper 1", year=2018, url="https://paper1.com", collection=self.collection
        )
        Paper.objects.create(
            title="Paper 2", year=2019, url="https://paper2.com", collection=self.collection
        )
        sample = Sample.objects.create(collection=self.collection)
        Execution.objects.create(collection=self.collection)
        Execution.objects.create(sample=sample)



class CollectionUpdatingTests(CollectionUpdateTest):
    
    def test_can_update_collection_ignoring_papers(self):
        result = self.client.execute("""mutation {
            updateCollection(id: 1 name: "New name" private: false description: "DDD") {
                collection { id name description private papers { title year url } }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
                {"title": "Paper 2", "year": 2019, "url": "https://paper2.com"},
            ]
        })
    

    def test_can_update_collection_adding_papers(self):
        result = self.client.execute("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                    {title: "Paper 3" year: 2020 url: "https://paper3.com"}
                ]
            ) {
                collection { id name description private papers { title year url } }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
                {"title": "Paper 2", "year": 2019, "url": "https://paper2.com"},
                {"title": "Paper 3", "year": 2020, "url": "https://paper3.com"},
            ]
        })


    def test_can_update_collection_removing_papers(self):
        result = self.client.execute("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                ]
            ) {
                collection { id name description private papers { title year url } }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
            ]
        })


    def test_can_update_collection_editing_papers(self):
        result = self.client.execute("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2 New" year: 2019 url: "https://paper2-new.com"}
                ]
            ) {
                collection { id name description private papers { title year url } }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
                {"title": "Paper 2 New", "year": 2019, "url": "https://paper2-new.com"},
            ]
        })


    def test_can_update_collection_no_papers_initially(self):
        self.collection.papers.all().delete()
        result = self.client.execute("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) {
                collection { id name description private papers { title year url } }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
                {"title": "Paper 2", "year": 2019, "url": "https://paper2.com"},
            ]
        })


    def test_collection_updating_validation(self):
        # Collection must exist
        self.check_query_error("""mutation {
            updateCollection(
                id: 2 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="Does not exist")

        # Collection must be viewable by user
        Collection.objects.create(id=2, name="Other")
        self.check_query_error("""mutation {
            updateCollection(
                id: 2 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="Does not exist")

        # Collection must be editable by user
        self.link.permission = 1
        self.link.save()
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="permission to edit")

        # Collection name must be short enough
        self.link.permission = 2
        self.link.save()
        name = f'"{"N" * 201}"'
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: """ + name + """ private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="200 characters")

        # Paper titles must be short enough
        title = f'"{"N" * 251}"'
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: """ + title + """ year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="250 characters")

        # Paper URLs must be valid
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "paper1com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="valid URL")

        # User must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: "New name" private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="Not authorized")



class CollectionDeletingTests(CollectionUpdateTest):
    
    def test_can_delete_collection(self):
        # Delete collection
        result = self.client.execute(
            """mutation { deleteCollection(id: "1") { success } }"""
        )

        # The collection is gone, as are the children
        self.assertTrue(result["data"]["deleteCollection"]["success"])
        self.assertFalse(Collection.objects.filter(id=1).count())
        self.assertEqual(Paper.objects.count(), 0)
        self.assertEqual(Sample.objects.count(), 0)
        self.assertEqual(Execution.objects.count(), 0)
    

    def test_collection_deletion_validation(self):
        # Collection must exist
        self.check_query_error(
            """mutation { deleteCollection(id: "10") { success } }""",
            message="Does not exist"
        )
        
        # Must be accessible
        Collection.objects.create(id=2)
        self.check_query_error(
            """mutation { deleteCollection(id: "2") { success } }""",
            message="Does not exist"
        )

        # You must be owner
        self.link.permission = 3
        self.link.save()
        self.check_query_error(
            """mutation { deleteCollection(id: "1") { success } }""",
            message="Not an owner"
        )

        # Must be signed in
        self.link.permission = 4
        self.link.save()
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteCollection(id: "1") { success } }""",
            message="Not authorized"
        )