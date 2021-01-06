import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Group, Paper

class CollectionSavingTests(TestCase):

    def test_can_create_collection(self):
        user = mixer.blend(User)
        collection = Collection.objects.create(name="collection", owner=user)
        self.assertTrue(collection.private)
        self.assertEqual(collection.description, "")
        self.assertLess(abs(collection.creation_time - time.time()), 1)
        self.assertLess(abs(collection.last_modified - time.time()), 1)
        self.assertFalse(collection.users.all())
        self.assertFalse(collection.groups.all())
        self.assertFalse(collection.papers.all())
    

    def test_can_update_collection(self):
        collection = mixer.blend(Collection, creation_time=0, last_modified=0)
        collection.description = "X"
        collection.save()
        self.assertLess(abs(collection.last_modified - time.time()), 1)
        self.assertGreater(abs(collection.creation_time - time.time()), 1)



class CollectionOrderingTests(TestCase):

    def test_collections_ordered_by_creation_time(self):
        collection1 = mixer.blend(Collection, creation_time=2)
        collection2 = mixer.blend(Collection, creation_time=1)
        collection3 = mixer.blend(Collection, creation_time=4)
        self.assertEqual(
            list(Collection.objects.all()), [collection2, collection1, collection3]
        )



class CollectionUsersTests(TestCase):
    
    def test_collection_users(self):
        collection = mixer.blend(Collection)
        user1 = mixer.blend(User)
        collection.users.add(user1)
        self.assertEqual(list(collection.users.all()), [user1])
        self.assertTrue(collection.collectionuserlink_set.get(user=user1).can_edit)
        self.assertFalse(collection.collectionuserlink_set.get(user=user1).can_execute)
        self.assertFalse(collection.users.filter(collectionuserlink__can_edit=False))
        self.assertFalse(collection.users.filter(collectionuserlink__can_execute=True))



class CollectionGroupsTests(TestCase):
    
    def test_collection_groups(self):
        collection = mixer.blend(Collection)
        group1 = mixer.blend(Group)
        collection.groups.add(group1)
        self.assertEqual(list(collection.groups.all()), [group1])
        self.assertTrue(collection.collectiongrouplink_set.get(group=group1).can_edit)
        self.assertFalse(collection.collectiongrouplink_set.get(group=group1).can_execute)
        self.assertFalse(collection.groups.filter(collectiongrouplink__can_edit=False))
        self.assertFalse(collection.groups.filter(collectiongrouplink__can_execute=True))



class CollectionPapersTests(TestCase):
    
    def test_collection_papers(self):
        collection = mixer.blend(Collection)
        paper1 = mixer.blend(Paper)
        collection.papers.add(paper1)
        self.assertEqual(list(collection.papers.all()), [paper1])