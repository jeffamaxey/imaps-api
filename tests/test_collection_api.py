from core.models import User, Group, UserGroupLink
from analysis.models import Collection, Sample, Paper, CollectionUserLink, CollectionGroupLink
from execution.models import Execution, Command
from .base import FunctionalTest

class CollectionQueryTests(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.collection = Collection.objects.create(
            id=1, name="Coll", description="My collection.", created=1000000, private=False
        )
        Paper.objects.create(year=2019, title="My paper", url="http://paper.com", collection=self.collection)
        Paper.objects.create(year=2018, title="My 1st paper", url="http://paper.com", collection=self.collection)
        Paper.objects.create(year=2020, title="Other paper", url="http://paper.com", collection=Collection.objects.create())
        CollectionUserLink.objects.create(collection=self.collection, user=User.objects.create(
            username="james", name="james", email="james@gmail.com"
        ), permission=4)
        CollectionUserLink.objects.create(collection=self.collection, user=User.objects.create(
            username="Kate", name="kate", email="kate@gmail.com"
        ), permission=4)
        CollectionUserLink.objects.create(collection=self.collection, user=User.objects.create(
            username="john", name="John", email="john@gmail.com"
        ))
        self.collection.samples.add(Sample.objects.create(
            name="run1", organism="human", source="ecoli", pi_name="John", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1000
        ))
        self.collection.samples.add(Sample.objects.create(
            name="run2", organism="human", source="ecoli", pi_name="John", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1001
        ))
        self.collection.samples.add(Sample.objects.create(
            name="run3", organism="mouse", source="ecoli", pi_name="Sarah", private=False,
            annotator_name="adam", qc_pass=False, qc_message="fail", created=1002
        ))
        self.collection.samples.add(Sample.objects.create(
            name="run4", organism="mouse", source="ecoli", pi_name="Sarah", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1003
        ))
        self.collection.samples.add(Sample.objects.create(
            name="run5", organism="mouse", source="ecoli", pi_name="Sarah", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1004
        ))
        Sample.objects.create(
            name="run6", organism="mouse", source="ecoli", pi_name="John", private=False,
            annotator_name="adam", qc_pass=True, qc_message="success", created=1005
        )
        self.collection.executions.add(Execution.objects.create(
            id=1, name="command1", private=False, created=1001,
            command=Command.objects.create(name="Command 1", description="Runs analysis 1")
        ))
        self.collection.executions.add(Execution.objects.create(
            id=2, name="command2", private=False, created=1002,
            command=Command.objects.create(name="Command 2", description="Runs analysis 2")
        ))
        self.collection.executions.add(Execution.objects.create(
            id=3, name="command3", private=False, created=1003,
            command=Command.objects.create(name="Command 3", description="Runs analysis 3")
        ))
        self.collection.executions.add(Execution.objects.create(
            id=4, name="command4", private=False, created=1004,
            command=Command.objects.create(name="Command 4", description="Runs analysis 4")
        ))
        self.collection.executions.add(Execution.objects.create(
            id=5, name="command5", private=False, created=1005,
            command=Command.objects.create(name="Command 5", description="Runs analysis 5")
        ))
        Execution.objects.create(
            id=6, name="command6", private=False, created=1006,
            command=Command.objects.create(name="Command 6", description="Runs analysis 6")
        )


    def test_can_get_collection(self):
        result = self.client.execute("""{ collection(id: "1") {
            name description created isOwner canShare canEdit
            papers { year title url } owners { name username }
            users { username collectionPermission(id: "1")}
            samples {
                name organism source piName annotatorName qcPass qcMessage created
            }
            executions { name created command { name description } }
        } }""")

        self.assertEqual(result["data"]["collection"], {
            "name": "Coll", "description": "My collection.", "created": 1000000, "papers": [
                {"year": 2018, "title": "My 1st paper", "url": "http://paper.com"},
                {"year": 2019, "title": "My paper", "url": "http://paper.com"}
            ],
            "isOwner": False, "canShare": False, "canEdit": False,
            "owners": [{"name": "james", "username": "james"}, {"name": "kate", "username": "Kate"}],
            "users": [
                {"username": "james", "collectionPermission": 4},
                {"username": "Kate", "collectionPermission": 4},
                {"username": "john", "collectionPermission": 1}
            ],
            "samples": [{
                "name": "run5", "organism": "mouse", "source": "ecoli",
                "piName": "Sarah", "annotatorName": "adam", "qcPass": True,
                "qcMessage": "success", "created": 1004
            }, {
                "name": "run4", "organism": "mouse", "source": "ecoli",
                "piName": "Sarah", "annotatorName": "adam", "qcPass": True,
                "qcMessage": "success", "created": 1003
            }, {
                "name": "run3", "organism": "mouse", "source": "ecoli",
                "piName": "Sarah", "annotatorName": "adam", "qcPass": False,
                "qcMessage": "fail", "created": 1002
            }, {
                "name": "run2", "organism": "human", "source": "ecoli",
                "piName": "John", "annotatorName": "adam", "qcPass": True,
                "qcMessage": "success", "created": 1001
            }, {
                "name": "run1", "organism": "human", "source": "ecoli",
                "piName": "John", "annotatorName": "adam", "qcPass": True,
                "qcMessage": "success", "created": 1000
            }],
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
    

    def test_can_detect_various_permissions_on_collection(self):
        # No link
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": False, "canEdit": False
        })

        # View access
        link = CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=1)
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": False, "canEdit": False
        })

        # Edit access
        link.permission = 2
        link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Share access
        link.permission = 3
        link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Owner access
        link.permission = 4
        link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": True, "canShare": True, "canEdit": True
        })

        # Group with lower permission
        group = Group.objects.create(name="Group 1")
        UserGroupLink.objects.create(user=self.user, group=group, permission=2)
        group_link = CollectionGroupLink.objects.create(collection=self.collection, group=group, permission=3)
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": True, "canShare": True, "canEdit": True
        })

        # Group can share, user can edit
        link.permission = 2
        link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": True, "canEdit": True
        })

        # Group can edit, user can view
        link.permission = 1
        link.save()
        group_link.permission = 2
        group_link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": False, "canEdit": True
        })

        # Group can view, user cannot
        link.delete()
        group_link.permission = 1
        group_link.save()
        result = self.client.execute("""{ collection(id: "1") {
            isOwner canShare canEdit
        } }""")
        self.assertEqual(result["data"]["collection"], {
            "isOwner": False, "canShare": False, "canEdit": False
        })
    

    def test_cant_get_collection(self):
        # Does not exist
        self.check_query_error("""{ collection(id: "100") { name } }""", message="Does not exist")

        # Not accessible
        self.collection.private = True
        self.collection.save()
        self.check_query_error("""{ collection(id: "1") { name } }""", message="Does not exist")