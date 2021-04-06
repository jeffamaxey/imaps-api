import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Sample, Group

class SampleSavingTests(TestCase):

    def test_can_create_sample(self):
        sample = Sample.objects.create(
            name="sample n", source="some cells", organism="humans", qc_pass=True,
            qc_message="very good", pi_name="Dr Smith", annotator_name="Jo",
        )
        self.assertLess(abs(sample.created - time.time()), 1)
        self.assertIsNone(sample.collection)
        self.assertLess(abs(sample.last_modified - time.time()), 1)
        self.assertFalse(sample.executions.all())
        self.assertEqual(str(sample), "sample n")
    

    def test_can_update_sample(self):
        sample = mixer.blend(Sample, created=0, last_modified=0)
        sample.description = "X"
        sample.save()
        self.assertLess(abs(sample.last_modified - time.time()), 1)
        self.assertGreater(abs(sample.created - time.time()), 1)



class SampleQuerysetViewableByTests(TestCase):

    def test_no_user(self):
        s1 = mixer.blend(Sample, private=True)
        s2 = mixer.blend(Sample, private=True)
        s3 = mixer.blend(Sample, private=False)
        s4 = mixer.blend(Sample, private=False)
        with self.assertNumQueries(1):
            self.assertEqual(list(Sample.objects.all().viewable_by(None)), [s3, s4])
    

    def test_user_access(self):
        user = mixer.blend(User)
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        group1.users.add(user)
        group2.users.add(user)
        samples = [
            mixer.blend(Sample, private=True),
            mixer.blend(Sample, private=False), # public
            mixer.blend(Sample, private=True), # accessible to user
            mixer.blend(Sample, private=True, collection=mixer.blend(Collection)), # collection belongs to user
            mixer.blend(Sample, private=True, sample=mixer.blend(Sample, collection=mixer.blend(Collection))), # collection belongs to group 1
            mixer.blend(Sample, private=True, sample=mixer.blend(Sample, collection=mixer.blend(Collection))), # collection belongs to group 2
            mixer.blend(Sample, private=True),
            mixer.blend(Sample, private=True),
            mixer.blend(Sample, private=True),
            mixer.blend(Sample, private=True),
            mixer.blend(Sample, private=True),
        ]
        samples[2].users.add(user)
        samples[3].collection.users.add(user)
        samples[4].collection.groups.add(group1)
        samples[5].collection.groups.add(group2)
        with self.assertNumQueries(2):
            self.assertEqual(list(Sample.objects.all().viewable_by(user)), samples[1:6])



class SampleOrderingTests(TestCase):

    def test_samples_ordered_by_created(self):
        sample1 = mixer.blend(Sample, created=2)
        sample2 = mixer.blend(Sample, created=1)
        sample3 = mixer.blend(Sample, created=4)
        self.assertEqual(
            list(Sample.objects.all()), [sample3, sample1, sample2]
        )