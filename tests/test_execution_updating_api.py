from core.models import User
from samples.models import Collection, Sample
from execution.models import Execution, Command, ExecutionUserLink
from .base import FunctionalTest

class ExecutionUpdateTest(FunctionalTest):
    
    def setUp(self):
        FunctionalTest.setUp(self)
        self.execution = Execution.objects.create(
            id=1, name="Execution 1", private=True
        )
        self.link = ExecutionUserLink.objects.create(execution=self.execution, user=self.user, permission=2)



class ExecutionUpdatingTests(ExecutionUpdateTest):
    
    def test_can_update_execution(self):
        result = self.client.execute("""mutation {
            updateExecution(id: 1 name: "New name" private: false) { execution { id name private } }
        }""")
        self.assertEqual(result["data"]["updateExecution"]["execution"], {
            "id": "1", "name": "New name", "private": False
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

        # Can't change private if sample or collection
        self.execution.sample = Sample.objects.create(private=True)
        self.execution.save()
        result = self.client.execute("""mutation {
            updateExecution(
                id: 1 name: "New name" private: false
            ) { execution { id private} }
        }""")
        self.assertTrue(result["data"]["updateExecution"]["execution"]["private"])
        self.execution.collection = Collection.objects.create(private=True)
        self.execution.sample = None
        self.execution.save()
        result = self.client.execute("""mutation {
            updateExecution(
                id: 1 name: "New name" private: false
            ) { execution { id private} }
        }""")
        self.assertTrue(result["data"]["updateExecution"]["execution"]["private"])

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



class ExecutionAccessTests(ExecutionUpdateTest):

    def setUp(self):
        ExecutionUpdateTest.setUp(self)
        self.user2 = User.objects.create(id=2, email="jon@gmail.com", username="jon")
        self.user3 = User.objects.create(id=3, email="sam@gmail.com", username="sam")
        self.link2 = ExecutionUserLink.objects.create(user=self.user2, execution=self.execution, permission=1)
        self.link.permission = 3
        self.link.save()


    def test_can_change_execution_user_permission(self):
        result = self.client.execute("""mutation { updateExecutionAccess(
            id: "1" user: "2" permission: 3
        ) { 
            execution { name }
            user { username }
        } }""")
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.permission, 3)
    

    def test_can_add_execution_user_link(self):
        self.link.permission = 3
        self.link.save()
        result = self.client.execute("""mutation { updateExecutionAccess(
            id: "1" user: "3" permission: 3
        ) { 
            execution { name }
            user { username }
        } }""")
        link = ExecutionUserLink.objects.get(execution=self.execution, user=self.user3)
        self.assertEqual(link.permission, 3)
    

    def test_can_remove_execution_user_link(self):
        result = self.client.execute("""mutation { updateExecutionAccess(
            id: "1" user: "2" permission: 0
        ) { 
            execution { name }
            user { username }
        } }""")
        self.assertFalse(ExecutionUserLink.objects.filter(execution=self.execution, user=self.user2))
    

    def test_execution_access_validation(self):
        # Execution must exist
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "100" user: "1" permission: 3
        ) { 
            execution {  name }
        } }""", message="Does not exist")

        # Execution must be accessible
        Collection.objects.create(id=23)
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "23" user: "1" permission: 3
        ) { 
            execution { name }
        } }""", message="Does not exist")

        # User must have share permissions on Execution (either directly or via collection/group)
        self.link.permission = 2
        self.link.save()
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "1" permission: 2
        ) { 
            execution { name }
        } }""", message="permission")
        self.link.permission = 3
        self.link.save()

        # User must exist
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "100" permission: 3
        ) { 
            execution {  name }
        } }""", message="Does not exist")

        # Permission must be valid for user
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "2" permission: -1
        ) { 
            execution { name }
        } }""", message="valid permission")
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "2" permission: 5
        ) { 
            execution { name }
        } }""", message="valid permission")

        # Only owners can create new owners
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "1" permission: 4
        ) { 
            execution { name }
        } }""", message="owner")

        # Only owners can demote owners
        self.link2.permission = 4
        self.link2.save()
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "2" permission: 3
        ) { 
            execution { name }
        } }""", message="owner")

        # Must be signed in
        del self.client.headers["Authorization"]
        self.check_query_error("""mutation { updateExecutionAccess(
            id: "1" user: "1" permission: 3
        ) { 
            execution { name }
        } }""", message="Not authorized")



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