from core.models import *
from .base import FunctionalTest

class SampleUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        collection1 = Collection.objects.create(
            id=1, name="My Collection", private=True,
            description="Collection desc"
        )
        collection2 = Collection.objects.create(
            id=2, name="My Other Collection", private=True,
            description="Collection 2 desc"
        )
        self.sample = Sample.objects.create(
            id=1, name="Sample 1", collection=collection1, pi_name="Dr Smith",
            annotator_name="Angelina", source="P452", organism="Felis catus"
        )
        self.link = SampleUserLink.objects.create(sample=self.sample, user=self.user, permission=2)
        self.c_link = CollectionUserLink.objects.create(collection=collection2, user=self.user, permission=4)



class SampleUpdatingTests(SampleUpdateTest):
    
    def test_can_update_sample(self):
        result = self.client.execute("""mutation {
            updateSample(id: 1 name: "New name" collection: "2" organism: "Homo sapiens" source: "XXX" piName: "Dr Jones" annotatorName: "James") {
                sample { id name collection { name } organism source piName annotatorName }
            }
        }""")
        self.assertEqual(result["data"]["updateSample"]["sample"], {
            "id": "1", "name": "New name", "source": "XXX", "piName": "Dr Jones",
            "annotatorName": "James", "organism": "Homo sapiens",
            "collection": {"name": "My Other Collection"}
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
                id: 1 source: """ + name + """ collection: "2" organism: "Homo sapiens"
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
