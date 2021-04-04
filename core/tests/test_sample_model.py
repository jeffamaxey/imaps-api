import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Sample

class SampleSavingTests(TestCase):

    def test_can_create_sample(self):
        collection = mixer.blend(Collection)
        sample = Sample.objects.create(
            name="sample", source="some cells", organism="humans", qc_pass=True,
            qc_message="very good", pi_name="Dr Smith", annotator_name="Jo",
            collection=collection
        )
        self.assertLess(abs(sample.created - time.time()), 1)
        self.assertLess(abs(sample.last_modified - time.time()), 1)
        self.assertFalse(sample.executions.all())
    

    def test_can_update_sample(self):
        sample = mixer.blend(Sample, created=0, last_modified=0)
        sample.description = "X"
        sample.save()
        self.assertLess(abs(sample.last_modified - time.time()), 1)
        self.assertGreater(abs(sample.created - time.time()), 1)



class SampleOrderingTests(TestCase):

    def test_samples_ordered_by_created(self):
        sample1 = mixer.blend(Sample, created=2)
        sample2 = mixer.blend(Sample, created=1)
        sample3 = mixer.blend(Sample, created=4)
        self.assertEqual(
            list(Sample.objects.all()), [sample3, sample1, sample2]
        )