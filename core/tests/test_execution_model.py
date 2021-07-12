import time
import json
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import Execution, Command, ExecutionUserLink, User, Group, Sample, Collection

class ExecutionSavingTests(TestCase):

    def test_can_create_execution(self):
        command = mixer.blend(Command)
        execution = Execution.objects.create(
            name="run-code (sample)", command=command, input="{}", output="{}",
        )
        execution.full_clean()
        self.assertIsNone(execution.started)
        self.assertIsNone(execution.finished)
        self.assertIsNone(execution.collection)
        self.assertIsNone(execution.sample)
        self.assertLess(abs(execution.created - time.time()), 1)
        self.assertEqual(str(execution), "run-code (sample)")



class ExecutionQuerysetViewableByTests(TestCase):

    def test_no_user(self):
        ex1 = mixer.blend(Execution, private=True)
        ex2 = mixer.blend(Execution, private=True)
        ex3 = mixer.blend(Execution, private=False)
        ex4 = mixer.blend(Execution, private=False)
        with self.assertNumQueries(1):
            self.assertEqual(list(Execution.objects.all().viewable_by(None)), [ex3, ex4])
    

    def test_user_access(self):
        user = mixer.blend(User)
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        group1.users.add(user)
        group2.users.add(user)
        executions = [
            mixer.blend(Execution, private=True),
            mixer.blend(Execution, private=False), # public
            mixer.blend(Execution, private=True), # belongs to user
            mixer.blend(Execution, private=True, sample=mixer.blend(Sample)), # sample belongs to user
            mixer.blend(Execution, private=True, sample=mixer.blend(Sample, collection=mixer.blend(Collection))), # sample collection belongs to user
            mixer.blend(Execution, private=True, collection=mixer.blend(Collection)), # collection belongs to user
            mixer.blend(Execution, private=True, sample=mixer.blend(Sample, collection=mixer.blend(Collection))), # collection belongs to group 1
            mixer.blend(Execution, private=True, collection=mixer.blend(Collection)), # sample collection belongs to group 1
            mixer.blend(Execution, private=True, sample=mixer.blend(Sample, collection=mixer.blend(Collection))), # collection belongs to group 2
            mixer.blend(Execution, private=True, collection=mixer.blend(Collection)), # sample collection belongs to group 2
            mixer.blend(Execution, private=True),
            mixer.blend(Execution, private=True),
            mixer.blend(Execution, private=True),
            mixer.blend(Execution, private=True),
            mixer.blend(Execution, private=True),
        ]
        executions[2].users.add(user)
        executions[3].sample.users.add(user)
        executions[4].sample.collection.users.add(user)
        executions[5].collection.users.add(user)
        executions[6].sample.collection.groups.add(group1)
        executions[7].collection.groups.add(group1)
        executions[8].sample.collection.groups.add(group2)
        executions[9].collection.groups.add(group2)
        with self.assertNumQueries(2):
            self.assertEqual(list(Execution.objects.all().viewable_by(user)), executions[1:10])



class ExecutionOrderingTests(TestCase):

    def test_samples_ordered_by_creation_time(self):
        ex1 = mixer.blend(Execution, created=2)
        ex2 = mixer.blend(Execution, created=1)
        ex3 = mixer.blend(Execution, created=4)
        self.assertEqual(
            list(Execution.objects.all()), [ex2, ex1, ex3]
        )



class ExecutionObjectsAccessTests(TestCase):

    def test_execution_users(self):
        execution = mixer.blend(Execution)
        self.assertFalse(execution.owners.count())
        self.assertFalse(execution.sharers.count())
        self.assertFalse(execution.editors.count())
        self.assertFalse(execution.users.count())
        u1, u2, u3, u4 = [mixer.blend(User) for _ in range(4)]
        link1 = ExecutionUserLink.objects.create(execution=execution, user=u1, permission=1)
        link2 = ExecutionUserLink.objects.create(execution=execution, user=u2, permission=2)
        link3 = ExecutionUserLink.objects.create(execution=execution, user=u3, permission=3)
        link3 = ExecutionUserLink.objects.create(execution=execution, user=u4, permission=4)
        self.assertEqual(set(execution.owners), {u4})
        self.assertEqual(set(execution.sharers), {u3, u4})
        self.assertEqual(set(execution.editors), {u2, u3, u4})
        self.assertEqual(set(execution.users.all()), {u1, u2, u3, u4})