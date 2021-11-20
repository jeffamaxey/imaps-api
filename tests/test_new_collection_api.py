from .base import FunctionalTest
from analysis.models import Collection

class CollectionCreationTests(FunctionalTest):

    def test_can_create_collection(self):
        result = self.client.execute("""mutation {
            createCollection(name: "New Collection" description: "Data" private: false) {
                collection { name description private owners { name } }
            }
        }""")
        self.assertEqual(result["data"]["createCollection"]["collection"], {
            "name": "New Collection", "description": "Data", "private": False,
            "owners": [{"name": "Adam A"}]
        })
    

    def test_collection_creation_validation(self):
        # Name must be unique
        Collection.objects.create(name="N")
        self.check_query_error("""mutation {
            createCollection(name: "N" description: "Data" private: false) {
                collection { name description private owners { name } }
            }
        }""", message="already exists")

        # Name must be short enough
        name = f'"{"N" * 151}"'
        self.check_query_error("""mutation {
            createCollection(name: """ + name + """ description: "Data" private: false) {
                collection { name description private owners { name } }
            }
        }""", message="150 characters")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            createCollection(name: "N" description: "Data" private: false) {
                collection { name description private owners { name } }
            }
        }""", message="Not authorized")