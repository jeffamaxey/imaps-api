import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Group, Paper, CollectionUserLink, CollectionGroupLink

class CollectionSavingTests(TestCase):

    def test_can_create_collection(self):
        collection = Collection.objects.create(name="collection")
        self.assertTrue(collection.private)
        self.assertEqual(collection.description, "")
        self.assertLess(abs(collection.created - time.time()), 1)
        self.assertLess(abs(collection.last_modified - time.time()), 1)
        self.assertFalse(collection.users.all())
        self.assertFalse(collection.groups.all())
        self.assertFalse(collection.papers.all())
        self.assertFalse(collection.samples.all())
        self.assertFalse(collection.executions.all())
    

    def test_can_update_collection(self):
        collection = mixer.blend(Collection, created=0, last_modified=0)
        collection.description = "X"
        collection.save()
        self.assertLess(abs(collection.last_modified - time.time()), 1)
        self.assertGreater(abs(collection.created - time.time()), 1)



class CollectionOrderingTests(TestCase):

    def test_collections_ordered_by_created(self):
        collection1 = mixer.blend(Collection, created=2)
        collection2 = mixer.blend(Collection, created=1)
        collection3 = mixer.blend(Collection, created=4)
        self.assertEqual(
            list(Collection.objects.all()), [collection3, collection1, collection2]
        )



class CollectionPapersTests(TestCase):
    
    def test_collection_papers(self):
        collection = mixer.blend(Collection)
        paper1 = mixer.blend(Paper)
        collection.papers.add(paper1)
        self.assertEqual(list(collection.papers.all()), [paper1])