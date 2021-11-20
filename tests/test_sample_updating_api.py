from core.models import User, Group, UserGroupLink
from analysis.models import Collection, Sample, CollectionUserLink, CollectionGroupLink, SampleUserLink
from execution.models import Execution
from .base import FunctionalTest

class SampleUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        self.collection1 = Collection.objects.create(
            id=1, name="My Collection", private=True,
            description="Collection desc"
        )
        collection2 = Collection.objects.create(
            id=2, name="My Other Collection", private=True,
            description="Collection 2 desc"
        )
        self.sample = Sample.objects.create(
            id=1, name="Sample 1", collection=self.collection1, pi_name="Dr Smith",
            annotator_name="Angelina", source="P452", organism="Felis catus"
        )
        self.link = SampleUserLink.objects.create(sample=self.sample, user=self.user, permission=2)
        self.c_link = CollectionUserLink.objects.create(collection=collection2, user=self.user, permission=4)
        Execution.objects.create(sample=self.sample, private=True)



class SampleUpdatingTests(SampleUpdateTest):
    
    def test_can_update_sample(self):
        result = self.client.execute("""mutation {
            updateSample(id: 1 name: "New name" collection: "2" organism: "Homo sapiens" source: "XXX" piName: "Dr Jones" annotatorName: "James") {
                sample {
                    id name organism source piName annotatorName
                    collection { name }
                }
            }
        }""")
        self.assertEqual(result["data"]["updateSample"]["sample"], {
            "id": "1", "name": "New name", "source": "XXX", "piName": "Dr Jones",
            "annotatorName": "James", "organism": "Homo sapiens",
            "collection": {"name": "My Other Collection"},
        })
    

    def test_can_update_sample_privacy(self):
        self.sample.collection = None
        self.sample.save()
        result = self.client.execute("""mutation {
            updateSample(id: 1 name: "New name" organism: "Homo sapiens" source: "XXX" piName: "Dr Jones" annotatorName: "James" private: false) {
                sample {
                    id name private organism source piName annotatorName
                    collection { name } executions { private }
                }
            }
        }""")
        self.assertEqual(result["data"]["updateSample"]["sample"], {
            "id": "1", "name": "New name", "source": "XXX", "piName": "Dr Jones",
            "annotatorName": "James", "organism": "Homo sapiens", "private": False,
            "collection": None, "executions": [{"private": False}]
        })
    

    def test_sample_update_validation(self):
        # Sample must exist
        self.check_query_error("""mutation {
            updateSample(
                id: 1000 name: "New name" collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="Does not exist")

        # Sample must be accessible
        Sample.objects.create(id=2, private=True)
        self.check_query_error("""mutation {
            updateSample(
                id: 2 name: "New name" collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="Does not exist")

        # Sample must be editable
        self.link.permission = 1
        self.link.save()
        self.check_query_error("""mutation {
            updateSample(
                id: 1 name: "New name" collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="permission to edit")
        self.link.permission = 2
        self.link.save()

        # Name must be short enough
        name = f'"{"X" * 251}"'
        self.check_query_error("""mutation {
            updateSample(
                id: 1 name: """ + name + """ collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="250 characters")

        # Collection must exist
        self.check_query_error("""mutation {
            updateSample(
                id: 1 name: "New name" collection: "100" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="Does not exist")

        # Collection must be accessible
        Collection.objects.create(id=3, private=True)
        self.check_query_error("""mutation {
            updateSample(
                id: 1 name: "New name" collection: "3" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="Does not exist")

        # Collection must be owned by user
        self.c_link.permission = 3
        self.c_link.save()
        self.check_query_error("""mutation {
            updateSample(
                id: 1 name: "New name" collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James"
            ) { sample { id } }
        }""", message="not owned")
        self.c_link.permission = 4
        self.c_link.save()

        # Can't change privacy if there is a collection
        result = self.client.execute("""mutation {
            updateSample(
                id: 1 name: "New name" collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" annotatorName: "James" private: false
            ) { sample { id private} }
        }""")
        self.assertTrue(result["data"]["updateSample"]["sample"]["private"])


        # PI Name must be short enough
        name = f'"{"X" * 101}"'
        self.check_query_error("""mutation {
            updateSample(
                id: 1 piName: """ + name + """ collection: "2" organism: "Homo sapiens"
                source: "XXX" annotatorName: "Dr Jones" name: "James"
            ) { sample { id } }
        }""", message="100 characters")

        # Annotator Name must be short enough
        name = f'"{"X" * 101}"'
        self.check_query_error("""mutation {
            updateSample(
                id: 1 annotatorName: """ + name + """ collection: "2" organism: "Homo sapiens"
                source: "XXX" piName: "Dr Jones" name: "James"
            ) { sample { id } }
        }""", message="100 characters")

        # Source must be short enough
        source = f'"{"X" * 101}"'
        self.check_query_error("""mutation {
            updateSample(
                id: 1 source: """ + source + """ collection: "2" organism: "Homo sapiens"
                annotatorName: "XXX" piName: "Dr Jones" name: "James"
            ) { sample { id } }
        }""", message="100 characters")

        # Organism must be short enough
        organism = f'"{"X" * 101}"'
        self.check_query_error("""mutation {
            updateSample(
                id: 1 organism: """ + organism + """ collection: "2" source: "Homo sapiens"
                annotatorName: "XXX" piName: "Dr Jones" name: "James"
            ) { sample { id } }
        }""", message="100 characters")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            updateSample(
                id: 1 organism: "Homo sapiens" collection: "2" source: "Homo sapiens"
                annotatorName: "XXX" piName: "Dr Jones" name: "James"
            ) { sample { id } }
        }""", message="Not authorized")



class SampleAccessTests(SampleUpdateTest):

    def setUp(self):
        SampleUpdateTest.setUp(self)
        self.user2 = User.objects.create(id=2, email="jon@gmail.com", username="jon")
        self.user3 = User.objects.create(id=3, email="sam@gmail.com", username="sam")
        self.link2 = SampleUserLink.objects.create(user=self.user2, sample=self.sample, permission=1)
        self.link.permission = 3
        self.link.save()


    def test_can_change_sample_user_permission(self):
        result = self.client.execute("""mutation { updateSampleAccess(
            id: "1" user: "2" permission: 3
        ) { 
            sample { name }
            user { username }
        } }""")
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.permission, 3)


    def test_can_add_sample_user_link(self):
        self.link.permission = 3
        self.link.save()
        result = self.client.execute("""mutation { updateSampleAccess(
            id: "1" user: "3" permission: 3
        ) { 
            sample {  name }
            user { username }
        } }""")
        link = SampleUserLink.objects.get(sample=self.sample, user=self.user3)
        self.assertEqual(link.permission, 3)
    

    def test_can_remove_sample_user_link(self):
        result = self.client.execute("""mutation { updateSampleAccess(
            id: "1" user: "2" permission: 0
        ) { 
            sample {  name }
            user { username }
        } }""")
        self.assertFalse(SampleUserLink.objects.filter(sample=self.sample, user=self.user2))
    


    def test_can_update_via_group(self):
        self.link.delete()
        group = Group.objects.create(slug="group1")
        UserGroupLink.objects.create(user=self.user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=self.sample.collection, group=group, permission=3)
        result = self.client.execute("""mutation { updateSampleAccess(
            id: "1" user: "2" permission: 3
        ) { 
            sample { name }
            user { username }
        } }""")
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.permission, 3)


    def test_sample_access_validation(self):
        # Sample must exist
        self.check_query_error("""mutation { updateSampleAccess(
            id: "100" user: "1" permission: 3
        ) { 
            sample { name }
        } }""", message="Does not exist")

        # Sample must be accessible
        Collection.objects.create(id=23)
        self.check_query_error("""mutation { updateSampleAccess(
            id: "23" user: "1" permission: 3
        ) { 
            sample {  name }
        } }""", message="Does not exist")

        # User must have share permissions on Sample (either directly or via collection/group)
        self.link.permission = 2
        self.link.save()
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "1" permission: 2
        ) { 
            sample {  name }
        } }""", message="permission")
        group = Group.objects.create(slug="group1")
        UserGroupLink.objects.create(user=self.user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=self.sample.collection, group=group, permission=2)
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "1" permission: 2
        ) { 
            sample {  name }
        } }""", message="permission")
        self.link.permission = 3
        self.link.save()

        # User must exist
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "100" permission: 3
        ) { 
            sample {  name }
        } }""", message="Does not exist")

        # Permission must be valid for user
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "2" permission: -1
        ) { 
            sample {  name }
        } }""", message="valid permission")
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "2" permission: 5
        ) { 
            sample {  name }
        } }""", message="valid permission")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateSampleAccess(
            id: "1" user: "1" permission: 3
        ) { 
            sample {  name }
        } }""", message="Not authorized")



class SampleDeletingTests(SampleUpdateTest):
    
    def test_can_delete_sample(self):
        # Delete sample
        CollectionUserLink.objects.create(collection=self.collection1, user=self.user, permission=4)
        result = self.client.execute(
            """mutation { deleteSample(id: "1") { success } }"""
        )

        # The sample is gone, as are the children
        self.assertTrue(result["data"]["deleteSample"]["success"])
        self.assertFalse(Sample.objects.filter(id=1).count())
        self.assertEqual(Sample.objects.count(), 0)
        self.assertEqual(Execution.objects.count(), 0)
    

    def test_sample_deletion_validation(self):
        # Sample must exist
        self.check_query_error(
            """mutation { deleteSample(id: "10") { success } }""",
            message="Does not exist"
        )
        
        # Must be accessible
        Sample.objects.create(id=5)
        self.check_query_error(
            """mutation { deleteSample(id: "5") { success } }""",
            message="Does not exist"
        )

        # You must be owner
        self.check_query_error(
            """mutation { deleteSample(id: "1") { success } }""",
            message="Not an owner"
        )

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteSample(id: "1") { success } }""",
            message="Not authorized"
        )
