import time
from mixer.backend.django import mixer
from django.test import TestCase
from core.models import User, Collection, Group, Paper, CollectionUserLink, CollectionGroupLink

class CollectionSavingTests(TestCase):

    def test_can_create_collection(self):
        collection = Collection.objects.create(name="collection")
        self.assertTrue(collection.private)
        self.assertEqual(collection.description, "")
        self.assertEqual(str(collection), "collection")
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



class CollectionQuerysetViewableByTests(TestCase):

    def test_no_user(self):
        c1 = mixer.blend(Collection, private=True)
        c2 = mixer.blend(Collection, private=True)
        c3 = mixer.blend(Collection, private=False)
        c4 = mixer.blend(Collection, private=False)
        with self.assertNumQueries(1):
            self.assertEqual(list(Collection.objects.all().viewable_by(None)), [c3, c4])
    

    def test_user_access(self):
        user = mixer.blend(User)
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        group1.users.add(user)
        group2.users.add(user)
        collections = [
            mixer.blend(Collection, private=True),
            mixer.blend(Collection, private=False), # public
            mixer.blend(Collection, private=True), # collection belongs to user
            mixer.blend(Collection, private=True), # collection belongs to group 1
            mixer.blend(Collection, private=True), # collection belongs to group 2
            mixer.blend(Collection, private=True),
            mixer.blend(Collection, private=True),
            mixer.blend(Collection, private=True),
            mixer.blend(Collection, private=True),
        ]
        collections[2].users.add(user)
        collections[3].groups.add(group1)
        collections[4].groups.add(group2)
        with self.assertNumQueries(2):
            self.assertEqual(list(Collection.objects.all().viewable_by(user)), collections[1:5])



class CollectionOrderingTests(TestCase):

    def test_collections_ordered_by_created(self):
        collection1 = mixer.blend(Collection, created=2)
        collection2 = mixer.blend(Collection, created=1)
        collection3 = mixer.blend(Collection, created=4)
        self.assertEqual(
            list(Collection.objects.all()), [collection3, collection1, collection2]
        )



class CollectionObjectsAccessTests(TestCase):

    def test_collection_users(self):
        collection = mixer.blend(Collection)
        self.assertFalse(collection.owners.count())
        self.assertFalse(collection.sharers.count())
        self.assertFalse(collection.editors.count())
        self.assertFalse(collection.users.count())
        u1, u2, u3, u4 = [mixer.blend(User) for _ in range(4)]
        link1 = CollectionUserLink.objects.create(collection=collection, user=u1, permission=1)
        link2 = CollectionUserLink.objects.create(collection=collection, user=u2, permission=2)
        link3 = CollectionUserLink.objects.create(collection=collection, user=u3, permission=3)
        link3 = CollectionUserLink.objects.create(collection=collection, user=u4, permission=4)
        self.assertEqual(set(collection.owners), {u4})
        self.assertEqual(set(collection.sharers), {u3, u4})
        self.assertEqual(set(collection.editors), {u2, u3, u4})
        self.assertEqual(set(collection.users.all()), {u1, u2, u3, u4})


    def test_collection_groups(self):
        collection = mixer.blend(Collection)
        self.assertFalse(collection.group_sharers.count())
        self.assertFalse(collection.group_editors.count())
        self.assertFalse(collection.groups.count())
        g1, g2, g3 = [mixer.blend(Group) for _ in range(3)]
        link1 = CollectionGroupLink.objects.create(collection=collection, group=g1, permission=1)
        link2 = CollectionGroupLink.objects.create(collection=collection, group=g2, permission=2)
        link3 = CollectionGroupLink.objects.create(collection=collection, group=g3, permission=3)
        self.assertEqual(set(collection.group_sharers), {g3})
        self.assertEqual(set(collection.group_editors), {g2, g3})
        self.assertEqual(set(collection.groups.all()), {g1, g2, g3})