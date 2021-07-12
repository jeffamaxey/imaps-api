import json
from core.models import *
from .base import FunctionalTest

class ExecutionQueryTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        command = Command.objects.create(
            name="Investigate", description="Investigates file",
        )
        downsteam_command_1 = Command.objects.create(
            name="Downstream command 1",
        )
        downsteam_command_2 = Command.objects.create(
            name="Downstream command 2",
        )
        self.execution = Execution.objects.create(
            id=1, name="Investigate this file", created=1000, status="OK",
            warning="no warning", error="no error",
            command=command, private=False,
            input=json.dumps([
                {"name": "genome", "type": "data:genome:", "value": 10},
                {"name": "annotations", "type": "list:data:genome:", "value": [20, 30]},
                {"name": "count", "type": "basic:int:", "value": 23},
            ]),
            output=json.dumps([
                {"name": "steps", "type": "list:data:", "value": [50, 60]}
            ]),
            collection=Collection.objects.create(name="Coll 1", private=False),
            sample=Sample.objects.create(name="Sample 1", private=False),
            parent=Execution.objects.create(
                name="Pipeline", output=json.dumps([
                    {"name": "steps", "type": "list:data:", "value": [1, 2, 3]}
                ]),
            )
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
            execution=self.execution, user=User.objects.create(username="anna", email="anna@gmail.com"), permission=4
        )
        ExecutionUserLink.objects.create(
            execution=self.execution, user=User.objects.create(username="james", email="james@gmail.com"), permission=4
        )
        ExecutionUserLink.objects.create(
            execution=self.execution, user=User.objects.create(username="sarah", email="sarah@gmail.com"),
        )


    def test_can_get_execution(self):
        result = self.client.execute("""{ execution(id: "1") {
            id name created status warning error input output
            canEdit canShare isOwner
            sample { name } collection { name } owners { username }
            parent { name } upstream { name }
            downstream { name } children { name }
            command { name description }
        } }""")

        self.assertEqual(result["data"]["execution"], {
            "id": "1", "name": "Investigate this file", "created": 1000, "status": "OK", "warning": "no warning", "error": "no error",
            "input": '[{"name": "genome", "type": "data:genome:", "value": 10}, {"name": "annotations", "type": "list:data:genome:", "value": [20, 30]}, {"name": "count", "type": "basic:int:", "value": 23}]',
            "output": '[{"name": "steps", "type": "list:data:", "value": [50, 60]}]',
            "canEdit": False, "canShare": False, "isOwner": False,
            "sample": {"name": "Sample 1"}, "collection": {"name": "Coll 1"},
            "owners": [{"username": "anna"}, {"username": "james"}],
            "parent": {"name": "Pipeline"}, "upstream": [], "downstream": [], "children": [],
            "command": {"name": "Investigate", "description": "Investigates file"}
        })
    

    def test_can_detect_various_permissions_on_sample(self):
        # No link
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": False
        })

        # Collection can edit
        collection = Collection.objects.create(name="C1")
        link = CollectionUserLink.objects.create(user=self.user, collection=collection, permission=2)
        self.execution.collection = collection
        self.execution.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Collection can share
        link.permission = 3
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Collection is owned
        link.permission = 4
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": True, "canShare": True, "canEdit": True
        })

        # Collection is editable by group
        group = Group.objects.create(slug="g1")
        UserGroupLink.objects.create(user=self.user, group=group, permission=2)
        link.permission = 1
        link.save()
        g_link = CollectionGroupLink.objects.create(collection=collection, group=group, permission=2)
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Collection is shareable by group
        g_link.permission = 3
        g_link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Sample collection can edit
        sample = Sample.objects.create(collection=collection)
        self.execution.sample = sample
        self.execution.collection = None
        self.execution.save()
        g_link.permission = 1
        g_link.save()
        link.permission = 2
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Sample collection can share
        link.permission = 3
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Sample collection is owner
        link.permission = 4
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": True, "canShare": True, "canEdit": True
        })

        # Sample collection is editable by group
        link.permission = 1
        link.save()
        g_link.permission = 2
        g_link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Sample collection is shareable by group
        g_link.permission = 3
        g_link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Sample can edit
        sample.collection = None
        sample.save()
        link = SampleUserLink.objects.create(sample=sample, user=self.user, permission=2)
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Sample can share
        link.permission = 3
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Execution is directly editable
        self.execution.sample = None
        self.execution.save()
        link = ExecutionUserLink.objects.create(execution=self.execution, user=self.user, permission=2)
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Execution is directly shareable
        link.permission = 3
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Execution is directly owned
        link.permission = 4
        link.save()
        result = self.client.execute("""{ execution(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["execution"], {
            "isOwner": True, "canShare": True, "canEdit": True
        })
    

    def test_cant_get_execution(self):
        # Does not exist
        self.check_query_error("""{ sample(id: "1000") { name } }""", message="Does not exist")

        # Not accessible
        self.execution.private = True
        self.execution.save()
        self.check_query_error("""{ sample(id: "1") { name } }""", message="Does not exist")
