import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Group, Paper, CollectionUserLink, CollectionGroupLink

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
            list(Collection.objects.all()), [collection3, collection1, collection2]
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



class CollectionEditableTests(TestCase):

    def test_none_user_cant_edit(self):
        collection = mixer.blend(Collection)
        self.assertFalse(collection.editable_by(None))
    

    def test_owner_can_edit(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        collection = mixer.blend(Collection, owner=user)
        self.assertTrue(collection.editable_by(user))
        self.assertFalse(collection.editable_by(other))
    

    def test_editing_via_access(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        collection = mixer.blend(Collection)
        CollectionUserLink.objects.create(user=user, collection=collection, can_edit=True, can_execute=False)
        CollectionUserLink.objects.create(user=other, collection=collection, can_edit=False, can_execute=False)
        self.assertTrue(collection.editable_by(user))
        self.assertFalse(collection.editable_by(other))
    

    def test_editing_via_group_access(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        group = mixer.blend(Group)
        other_group = mixer.blend(Group)
        group.users.add(user)
        other_group.users.add(other)
        group.save()
        other_group.save()
        collection = mixer.blend(Collection)
        CollectionUserLink.objects.create(user=user, collection=collection, can_edit=False, can_execute=False)
        CollectionUserLink.objects.create(user=other, collection=collection, can_edit=False, can_execute=False)
        CollectionGroupLink.objects.create(group=group, collection=collection, can_edit=True, can_execute=False)
        CollectionGroupLink.objects.create(group=other_group, collection=collection, can_edit=False, can_execute=False)
        self.assertTrue(collection.editable_by(user))
        self.assertFalse(collection.editable_by(other))



class CollectionExecutableTests(TestCase):

    def test_none_user_cant_execute(self):
        collection = mixer.blend(Collection)
        self.assertFalse(collection.executable_by(None))
    

    def test_owner_can_execute(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        collection = mixer.blend(Collection, owner=user)
        self.assertTrue(collection.executable_by(user))
        self.assertFalse(collection.executable_by(other))
    

    def test_executeing_via_access(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        collection = mixer.blend(Collection)
        CollectionUserLink.objects.create(user=user, collection=collection, can_execute=True, can_edit=False)
        CollectionUserLink.objects.create(user=other, collection=collection, can_execute=False, can_edit=False)
        self.assertTrue(collection.executable_by(user))
        self.assertFalse(collection.executable_by(other))
    

    def test_executing_via_group_access(self):
        user = mixer.blend(User)
        other = mixer.blend(User)
        group = mixer.blend(Group)
        other_group = mixer.blend(Group)
        group.users.add(user)
        other_group.users.add(other)
        group.save()
        other_group.save()
        collection = mixer.blend(Collection)
        CollectionUserLink.objects.create(user=user, collection=collection, can_execute=False, can_edit=False)
        CollectionUserLink.objects.create(user=other, collection=collection, can_execute=False, can_edit=False)
        CollectionGroupLink.objects.create(group=group, collection=collection, can_execute=True, can_edit=False)
        CollectionGroupLink.objects.create(group=other_group, collection=collection, can_execute=False, can_edit=False)
        self.assertTrue(collection.executable_by(user))
        self.assertFalse(collection.executable_by(other))