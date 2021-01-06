from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from core.models import Group, Collection

class GroupCreationTests(TestCase):

    def test_can_create_group(self):
        group = Group.objects.create(name="Locke Lab")
        self.assertFalse(group.users.count())
        self.assertFalse(group.admins.count())
        self.assertFalse(group.group_invitations.count())
        self.assertFalse(group.collections.count())
        self.assertNotEqual(group.id, 1)
    

    def test_group_uniqueness(self):
        group = mixer.blend(
            Group, slug="Locke_Lab", description="A place where miracles happen"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Group.objects.create(slug="Locke_Lab")
        self.assertEqual(Group.objects.count(), 1)
    

    def test_group_slug_validation(self):
        group = mixer.blend(Group, slug="1")
        with self.assertRaises(ValidationError):
            group.full_clean()



class GroupCollectionsTests(TestCase):
    
    def test_can_get_collections_with_permissions(self):
        group = mixer.blend(Group)
        collection1 = mixer.blend(Collection)
        collection2 = mixer.blend(Collection)
        collection3 = mixer.blend(Collection)
        group.collections.add(collection1)
        group.collections.add(collection2)
        self.assertEqual(list(group.collections.all()), [collection1, collection2])
        self.assertTrue(group.collectiongrouplink_set.get(collection=collection1).can_edit)
        self.assertFalse(group.collectiongrouplink_set.get(collection=collection1).can_execute)
        self.assertFalse(group.collections.filter(collectiongrouplink__can_edit=False))
        self.assertFalse(group.collections.filter(collectiongrouplink__can_execute=True))