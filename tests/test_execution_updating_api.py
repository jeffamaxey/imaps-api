from core.models import *
from .base import FunctionalTest

class ExecutionUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        self.execution = Execution.objects.create(
            id=1, name="Execution 1"
        )
        self.link = ExecutionUserLink.objects.create(execution=self.execution, user=self.user, permission=2)



class ExecutionUpdatingTests(ExecutionUpdateTest):
    
    def test_can_update_execution(self):
        result = self.client.execute("""mutation {
            updateExecution(id: 1 name: "New name") { execution { id name } }
        }""")
        self.assertEqual(result["data"]["updateExecution"]["execution"], {
            "id": "1", "name": "New name"
        })
    

    def test_sample_update_validation(self):
        # Execution must exist
        self.check_query_error("""mutation {
            updateExecution(id: 100 name: "New name") { execution { id name } }
        }""", message="Does not exist")

        # Execution must be accessible
        Execution.objects.create(id=2, private=True)
        self.check_query_error("""mutation {
            updateExecution(id: 2 name: "New name") { execution { id name } }
        }""", message="Does not exist")

        # Execution must be editable
        self.link.permission = 1
        self.link.save()
        self.check_query_error("""mutation {
            updateExecution(id: 1 name: "New name") { execution { id name } }
        }""", message="permission to edit")
        self.link.permission = 2
        self.link.save()

        # Name must be short enough
        name = f'"{"X" * 251}"'
        self.check_query_error("""mutation {
            updateExecution(id: 1 name: """ + name + """) { execution { id name } }
        }""", message="250 characters")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation {
            updateExecution(id: 1 name: "New Name") { execution { id name } }
        }""", message="Not authorized")



class ExecutionDeletingTests(ExecutionUpdateTest):
    
    def test_can_delete_sample(self):
        # Delete execution
        ExecutionUserLink.objects.create(execution=self.execution, user=self.user, permission=4)
        result = self.client.execute(
            """mutation { deleteExecution(id: "1") { success } }"""
        )

        # The execution is gone
        self.assertTrue(result["data"]["deleteExecution"]["success"])
        self.assertFalse(Execution.objects.filter(id=1).count())
    

    def test_sample_deletion_validation(self):
        # Execution must exist
        self.check_query_error(
            """mutation { deleteExecution(id: "10") { success } }""",
            message="Does not exist"
        )
        
        # Must be accessible
        Execution.objects.create(id=5)
        self.check_query_error(
            """mutation { deleteExecution(id: "5") { success } }""",
            message="Does not exist"
        )

        # You must be owner
        self.check_query_error(
            """mutation { deleteExecution(id: "1") { success } }""",
            message="Not an owner"
        )

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error(
            """mutation { deleteExecution(id: "1") { success } }""",
            message="Not authorized"
        )