from core.models import User, Group, UserGroupLink
from samples.models import Collection, Sample, Paper, CollectionUserLink, CollectionGroupLink
from execution.models import Execution, ExecutionUserLink
from .base import FunctionalTest

class CollectionUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        self.collection = Collection.objects.create(
            id=1, name="My Collection", private=True,
            description="Collection desc", last_modified=100
        )
        self.link = CollectionUserLink.objects.create(collection=self.collection, user=self.user, permission=4)
        Paper.objects.create(
            title="Paper 1", year=2018, url="https://paper1.com", collection=self.collection
        )
        Paper.objects.create(
            title="Paper 2", year=2019, url="https://paper2.com", collection=self.collection
        )
        sample = Sample.objects.create(collection=self.collection, private=True)
        Execution.objects.create(collection=self.collection)
        Execution.objects.create(sample=sample)



class CollectionUpdatingTests(CollectionUpdateTest):
    
    def test_can_update_collection_ignoring_papers(self):
        result = self.client.execute("""mutation {
            updateCollection(id: 1 name: "New name" private: false description: "DDD") {
                collection {
                    id name description private
                    papers { title year url }
                    samples { private executions { private } }
                    executions { private }
                }
            }
        }""")
        self.assertEqual(result["data"]["updateCollection"]["collection"], {
            "id": "1", "name": "New name", "description": "DDD", "private": False,
            "papers": [
                {"title": "Paper 1", "year": 2018, "url": "https://paper1.com"},
                {"title": "Paper 2", "year": 2019, "url": "https://paper2.com"},
            ],
            "samples": [{"private": False, "executions": [{"private": False}]}],
            "executions": [{"private": False}]
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
        name = f'"{"N" * 151}"'
        self.check_query_error("""mutation {
            updateCollection(
                id: 1 name: """ + name + """ private: false description: "DDD"
                papers: [
                    {title: "Paper 1" year: 2018 url: "https://paper1.com"}
                    {title: "Paper 2" year: 2019 url: "https://paper2.com"}
                ]
            ) { collection { id } }
        }""", message="150 characters")

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



class CollectionAccessTests(CollectionUpdateTest):

    def setUp(self):
        CollectionUpdateTest.setUp(self)
        self.user2 = User.objects.create(id=2, email="jon@gmail.com", username="jon")
        self.user3 = User.objects.create(id=3, email="sam@gmail.com", username="sam")
        self.link2 = CollectionUserLink.objects.create(user=self.user2, collection=self.collection, permission=1)
        self.group1 = Group.objects.create(id=1, name="Group 1", slug="group1")
        self.group2 = Group.objects.create(id=2, name="Group 2", slug="group2")
        self.link3 = CollectionGroupLink.objects.create(group=self.group1, collection=self.collection, permission=1)
        self.link.permission = 3
        self.link.save()


    def test_can_change_collection_user_permission(self):
        self.client.execute("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 3
        ) { 
            collection { name }
            user { username }
        } }""")
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.permission, 3)
    

    def test_can_change_collection_group_permission(self):
        self.client.execute("""mutation { updateCollectionAccess(
            id: "1" group: "1" permission: 3
        ) { 
            collection {  name  }
            group { slug }
        } }""")
        self.link3.refresh_from_db()
        self.assertEqual(self.link3.permission, 3)


    def test_can_add_collection_user_link(self):
        self.link.permission = 4
        self.link.save()
        self.client.execute("""mutation { updateCollectionAccess(
            id: "1" user: "3" permission: 4
        ) { 
            collection {  name }
            user { username }
        } }""")
        link = CollectionUserLink.objects.get(collection=self.collection, user=self.user3)
        self.assertEqual(link.permission, 4)


    def test_can_add_collection_group_permission(self):
        self.client.execute("""mutation { updateCollectionAccess(
            id: "1" group: "2" permission: 3
        ) { 
            collection {  name }
            group { slug }
        } }""")
        link = CollectionGroupLink.objects.get(collection=self.collection, group=self.group2)
        self.assertEqual(link.permission, 3)
    

    def test_can_remove_collection_user_link(self):
        result = self.client.execute("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 0
        ) { 
            collection { name }
            user { username }
        } }""")
        self.assertFalse(CollectionUserLink.objects.filter(collection=self.collection, user=self.user2))
    

    def test_can_remove_collection_group_permission(self):
        self.client.execute("""mutation { updateCollectionAccess(
            id: "1" group: "1" permission: 0
        ) { 
            collection {  name }
            group { slug }
        } }""")
        self.assertFalse(CollectionGroupLink.objects.filter(collection=self.collection, group=self.group1))
    

    def test_can_update_via_group(self):
        self.link.delete()
        UserGroupLink.objects.create(user=self.user, group=self.group1, permission=2)
        self.link3.permission = 3
        self.link3.save()
        result = self.client.execute("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 3
        ) { 
            collection {  name }
            user { username }
        } }""")
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.permission, 3)


    def test_collection_access_validation(self):
        # Collection must exist
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "100" group: "1" permission: 3
        ) { 
            collection {  name }
        } }""", message="Does not exist")

        # Collection must be accessible
        Collection.objects.create(id=23)
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "23" group: "1" permission: 3
        ) { 
            collection {  name }
        } }""", message="Does not exist")

        # User must have share permissions on collection (either directly or via group)
        self.link.permission = 2
        self.link.save()
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "1" permission: 2
        ) { 
            collection {  name }
        } }""", message="permission")
        UserGroupLink.objects.create(user=self.user, group=self.group1, permission=2)
        self.link3.permission = 2
        self.link3.save()
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "1" permission: 2
        ) { 
            collection {  name  }
        } }""", message="permission")
        self.link.permission = 3
        self.link.save()

        # User must exist
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "100" permission: 3
        ) { 
            collection {  name }
        } }""", message="Does not exist")

        # Group must exist
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "100" permission: 3
        ) { 
            collection {  name }
        } }""", message="Does not exist")

        # Either user or group must be provided
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" permission: 3
        ) { 
            collection {  name }
        } }""", message="user or group")

        # Permission must be valid for user
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: -1
        ) { 
            collection {  name  }
        } }""", message="valid permission")
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 5
        ) { 
            collection {  name  }
        } }""", message="valid permission")

        # Permission must be valid for group
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "2" permission: -1
        ) { 
            collection {  name }
        } }""", message="valid permission")
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "2" permission: 4
        ) { 
            collection {  name }
        } }""", message="valid permission")

        # Only owners can create new owners
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 4
        ) { 
            collection {  name }
        } }""", message="owner")

        # Only owners can demote owners
        self.link2.permission = 4
        self.link2.save()
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "2" permission: 3
        ) { 
            collection {  name }
        } }""", message="owner")

        # Must always be an owner
        self.link.permission = 4
        self.link2.permission = 3
        self.link.save()
        self.link2.save()
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" user: "1" permission: 3
        ) { 
            collection {  name }
        } }""", message="owner")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateCollectionAccess(
            id: "1" group: "1" permission: 3
        ) { 
            collection {  name }
        } }""", message="Not authorized")

