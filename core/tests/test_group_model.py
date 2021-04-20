from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from core.models import *

class GroupCreationTests(TestCase):

    def test_can_create_group(self):
        group = Group.objects.create(name="Locke Lab")
        self.assertFalse(group.users.count())
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



class GroupObjectsAccessTests(TestCase):

    def test_user_groups(self):
        group = mixer.blend(Group)
        self.assertFalse(group.admins.count())
        self.assertFalse(group.members.count())
        self.assertFalse(group.invitees.count())
        self.assertFalse(group.users.count())
        u1, u2, u3 = [mixer.blend(User) for _ in range(3)]
        link1 = UserGroupLink.objects.create(group=group, user=u1, permission=1)
        link2 = UserGroupLink.objects.create(group=group, user=u2, permission=2)
        link3 = UserGroupLink.objects.create(group=group, user=u3, permission=3)
        self.assertEqual(set(group.admins), {u3})
        self.assertEqual(set(group.members), {u2, u3})
        self.assertEqual(set(group.invitees), {u1})
    

    def test_group_collections(self):
        group = mixer.blend(Group)
        self.assertFalse(group.shareable_collections.count())
        self.assertFalse(group.editable_collections.count())
        self.assertFalse(group.collections.count())
        c1, c2, c3 = [mixer.blend(Collection) for _ in range(3)]
        link1 = CollectionGroupLink.objects.create(group=group, collection=c1, permission=1)
        link2 = CollectionGroupLink.objects.create(group=group, collection=c2, permission=2)
        link3 = CollectionGroupLink.objects.create(group=group, collection=c3, permission=3)
        self.assertEqual(set(group.shareable_collections), {c3})
        self.assertEqual(set(group.editable_collections), {c2, c3})
        self.assertEqual(set(group.collections.all()), {c1, c2, c3})