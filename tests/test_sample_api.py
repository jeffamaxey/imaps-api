from core.models import *
from .base import FunctionalTest

class SampleQueryTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.sample = Sample.objects.create(
            id=1, name="run1", organism="human", source="ecoli", pi_name="John", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1000
        )
        self.sample.collection = Collection.objects.create(name="Coll 1", private=False)
        self.sample.save()
  
        self.sample.executions.add(Execution.objects.create(
            id=1, name="command1", private=False, created=1001,
            command=Command.objects.create(name="Command 1", description="Runs analysis 1")
        ))
        self.sample.executions.add(Execution.objects.create(
            id=2, name="command2", private=False, created=1002,
            command=Command.objects.create(name="Command 2", description="Runs analysis 2")
        ))
        self.sample.executions.add(Execution.objects.create(
            id=3, name="command3", private=False, created=1003,
            command=Command.objects.create(name="Command 3", description="Runs analysis 3")
        ))
        self.sample.executions.add(Execution.objects.create(
            id=4, name="command4", private=False, created=1004,
            command=Command.objects.create(name="Command 4", description="Runs analysis 4")
        ))
        self.sample.executions.add(Execution.objects.create(
            id=5, name="command5", private=False, created=1005,
            command=Command.objects.create(name="Command 5", description="Runs analysis 5")
        ))
        Execution.objects.create(
            id=6, name="command6", private=False, created=1006,
            command=Command.objects.create(name="Command 6", description="Runs analysis 6")
        )


    def test_can_get_sample(self):
        result = self.client.execute("""{ sample(id: "1") {
            name organism source piName annotatorName qcPass qcMessage created
            collection { name }
            executions { name created command {
                name description
            } }
        } }""")
        self.assertEqual(result["data"]["sample"], {
           "name": "run1", "organism": "human", "source": "ecoli",
            "piName": "John", "annotatorName": "adam", "qcPass": True,
            "qcMessage": "success", "created": 1000,
            "collection": {"name": "Coll 1"},
            "executions": [{
                "name": "command1", "created": 1001,
                "command": {"name": "Command 1", "description": "Runs analysis 1"}
            }, {
                "name": "command2", "created": 1002,
                "command": {"name": "Command 2", "description": "Runs analysis 2"}
            }, {
                "name": "command3", "created": 1003,
                "command": {"name": "Command 3", "description": "Runs analysis 3"}
            }, {"name": "command4", "created": 1004,
                "command": {"name": "Command 4", "description": "Runs analysis 4"}
            }, {
                "name": "command5", "created": 1005,
                "command": {"name": "Command 5", "description": "Runs analysis 5"}
            }]
        })
    

    def test_cant_get_sample(self):
        # Does not exist
        self.check_query_error("""{ sample(id: "100") { name } }""", message="Does not exist")

        # Not accessible
        self.sample.private = True
        self.sample.save()
        self.check_query_error("""{ sample(id: "1") { name } }""", message="Does not exist")