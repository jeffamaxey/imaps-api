import json
from core.models import *
from .base import FunctionalTest

class ExecutionApiTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        user = User.objects.create(
            username="adam", email="adam@crick.ac.uk", name="Adam A",
        )
        command = Command.objects.create(
            name="Investigate", description="Investigates file",
            input_schema=json.dumps([
                {"name": "genome", "type": "data:genome:"},
                {"name": "annotations", "type": "list:data:genome:"},
                {"name": "count", "type": "basic:int:"},
            ]),
            output_schema=json.dumps([
                {"name": "steps", "type": "list:data:"}
            ])
        )
        downsteam_command_1 = Command.objects.create(
            name="Downstream command 1",
            input_schema=json.dumps([
                {"name": "genome", "type": "data:genome:"}
            ])
        )
        downsteam_command_2 = Command.objects.create(
            name="Downstream command 2",
            input_schema=json.dumps([
                {"name": "annotations", "type": "list:data:genome:"},
            ])
        )
        self.execution = Execution.objects.create(
            id=1, name="Investigate this file", created=1000, status="OK",
            warning="no warning", error="no error",
            command=command, private=False,
            input=json.dumps({
                "genome": 10, "annotations": [20, 30], "count": 23
            }),
            output=json.dumps({
                "steps": [50, 60]
            }),
            collection=Collection.objects.create(name="Coll 1", private=False),
            sample=Sample.objects.create(name="Sample 1", private=False),
        )

        parent_execution = Execution.objects.create(
            name="Pipeline", output=json.dumps({"steps": [1, 2, 3]}),
        )

        Execution.objects.create(id=10, name="Input E 1", private=False)
        Execution.objects.create(id=20, name="Input E 2", private=False)
        Execution.objects.create(id=30, name="Input E 3", private=False)

        Execution.objects.create(id=50, name="Step E 1", private=False)
        Execution.objects.create(id=60, name="Step E 2", private=False)

        Execution.objects.create(
            id=70, name="Downstream 1", private=False,
            command=downsteam_command_1, input=json.dumps({"genome": 1})
        )
        Execution.objects.create(
            id=80, name="Downstream 2", private=False,
            command=downsteam_command_1, input=json.dumps({"genome": 1})
        )
        Execution.objects.create(
            id=90, name="Downstream 3", private=False,
            command=downsteam_command_2, input=json.dumps({"annotations": [1]})
        )

        ExecutionUserLink.objects.create(
            execution=self.execution, user=User.objects.create(username="anna", email="anna@gmail.com"), is_owner=True
        )
        ExecutionUserLink.objects.create(
            execution=self.execution, user=User.objects.create(username="james", email="james@gmail.com"), is_owner=True
        )
        ExecutionUserLink.objects.create(
            execution=self.execution, user=User.objects.create(username="sarah", email="sarah@gmail.com"),
        )



class ExecutionQueryTests(ExecutionApiTests):
    '''
    input output

    command { id name description inputSchema outputSchema }
    downstreamExecutions { id started created finished name }
    '''

    def test_can_get_execution(self):
        result = self.client.execute("""{ execution(id: "1") {
            id name created status warning error input output
            sample { name } collection { name } owners { username }
            parent { name } upstreamExecutions { name }
            downstreamExecutions { name } componentExecutions { name }
            command { name description inputSchema outputSchema }
        } }""")

        self.assertEqual(result["data"]["execution"], {
            "id": "1", "name": "Investigate this file", "created": 1000,
            "status": "OK", "warning": "no warning", "error": "no error",
            "input": '{"genome": 10, "annotations": [20, 30], "count": 23}', "output": '{"steps": [50, 60]}',
            "collection": {"name": "Coll 1"}, "sample": {"name": "Sample 1"},
            "owners": [{"username": "anna"}, {"username": "james"}],
            "parent": {"name": "Pipeline"},
            "upstreamExecutions": [{"name": "Input E 1"}, {"name": "Input E 2"}, {"name": "Input E 3"}],
            "downstreamExecutions": [{"name": "Downstream 1"}, {"name": "Downstream 2"}, {"name": "Downstream 3"}],
            "componentExecutions": [{"name": "Step E 1"}, {"name": "Step E 2"}],
            "command": {
                "name": "Investigate", "description": "Investigates file",
                "inputSchema": '[{"name": "genome", "type": "data:genome:"}, {"name": "annotations", "type": "list:data:genome:"}, {"name": "count", "type": "basic:int:"}]',
                "outputSchema": '[{"name": "steps", "type": "list:data:"}]'
            }
        })
    

    def test_cant_get_execution(self):
        # Does not exist
        self.check_query_error("""{ sample(id: "1000") { name } }""", message="Does not exist")

        # Not accessible
        self.execution.private = True
        self.execution.save()
        self.check_query_error("""{ sample(id: "1") { name } }""", message="Does not exist")
