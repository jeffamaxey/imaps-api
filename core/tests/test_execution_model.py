import time
import json
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import Execution, Process

class ExecutionSavingTests(TestCase):

    def test_can_create_execution(self):
        process = mixer.blend(Process)
        execution = Execution.objects.create(
            name="run-code (sample)", process=process, input="{}", output="{}",

        )
        execution.full_clean()
        self.assertIsNone(execution.scheduled)
        self.assertIsNone(execution.started)
        self.assertIsNone(execution.finished)
        self.assertIsNone(execution.collection)
        self.assertIsNone(execution.sample)
        self.assertLess(abs(execution.created - time.time()), 1)
        self.assertEqual(str(execution), "run-code (sample)")



class ExecutionOrderingTests(TestCase):

    def test_samples_ordered_by_creation_time(self):
        ex1 = mixer.blend(Execution, created=2)
        ex2 = mixer.blend(Execution, created=1)
        ex3 = mixer.blend(Execution, created=4)
        self.assertEqual(
            list(Execution.objects.all()), [ex2, ex1, ex3]
        )



class ExecutionParentTests(TestCase):

    def test_can_get_no_parent(self):
        execution = mixer.blend(Execution)
        self.assertIsNone(execution.parent)
    

    def test_can_get_parent(self):
        execution = mixer.blend(Execution, id=24)
        ex1 = mixer.blend(Execution, output=json.dumps({"N1": [24]})),
        ex2 = mixer.blend(Execution, output=json.dumps({"N1": [23, 25]}))
        ex3 = mixer.blend(Execution, output=json.dumps({"steps": [23, 24]}))
        with self.assertNumQueries(1):
            self.assertEqual(execution.parent, ex3)



class ExecutionUpstreamTests(TestCase):

    def test_can_get_no_upstream(self):
        execution = mixer.blend(Execution)
        self.assertFalse(execution.upstream)
    

    def test_can_get_upstream(self):
        process = mixer.blend(Process, input_schema=json.dumps([
            {"name": "inp1", "type": "basic:json:"},
            {"name": "inp2", "type": "data:fasta:"},
            {"name": "inp3", "type": "list:data:seq"},
            {"name": "inp4"},
        ]))
        execution = mixer.blend(Execution, process=process, input=json.dumps({
            "inp1": 10, "inp2": 20, "inp3": [30, 40, 50], "inp4": 10
        }))
        ex1 = mixer.blend(Execution, id=10)
        ex2 = mixer.blend(Execution, id=20)
        ex3 = mixer.blend(Execution, id=30)
        ex4 = mixer.blend(Execution, id=40)
        with self.assertNumQueries(1):
            self.assertEqual(list(execution.upstream), [ex2, ex3, ex4])



class ExecutionDownstreamTests(TestCase):

    def test_can_get_no_downstream(self):
        execution = mixer.blend(Execution)
        self.assertFalse(execution.downstream)
    

    def test_can_get_downstream(self):
        ex1 = mixer.blend(Execution, input=json.dumps({
            "inp1": 1, "inp2": 2, "inp3": "xxx"
        }), process=mixer.blend(Process, input_schema=json.dumps([
            {"name": "inp1", "type": "data:fasta"},
            {"name": "inp2", "type": "data:fasta"},
            {"name": "inp3", "type": "basic:str"},
        ])))
        ex2 = mixer.blend(Execution, input=json.dumps({
            "inp1": [1, 2], "inp2": [3, 4], "inp3": "xxx"
        }), process=mixer.blend(Process, input_schema=json.dumps([
            {"name": "inp1", "type": "list:data:fasta"},
            {"name": "inp2", "type": "list:data:fasta"},
            {"name": "inp3", "type": "basic:str"},
        ])))
        ex3 = mixer.blend(Execution, input=json.dumps({
            "inp1": [1, 2], "inp2": [3, 4], "inp3": "xxx"
        }), process=mixer.blend(Process, input_schema=json.dumps([
            {"name": "inpx", "type": "list:data:fasta"},
            {"name": "inp2"},
            {"name": "inp3", "type": "basic:str"},
        ])))
        execution = mixer.blend(Execution, id=1)
        with self.assertNumQueries(2):
            self.assertEqual(set(execution.downstream), {ex1, ex2})



class ExecutionComponentTests(TestCase):

    def test_can_get_no_components(self):
        execution = mixer.blend(Execution)
        self.assertFalse(execution.components)
    

    def test_can_get_components(self):
        execution = mixer.blend(Execution, output=json.dumps({
            "inp1": [1, 2], "steps": [3, 4, 5]
        }))
        executions = [mixer.blend(Execution, id=n) for n in range(1, 5)]
        with self.assertNumQueries(1):
            self.assertEqual(set(execution.components), set(executions[2:4]))


