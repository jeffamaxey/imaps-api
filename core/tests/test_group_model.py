from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from core.models import Group

class GroupCreationTests(TestCase):

    def test_can_create_group(self):
        group = Group.objects.create(name="Locke Lab")
        self.assertFalse(group.users.count())
        self.assertFalse(group.admins.count())
        self.assertFalse(group.group_invitations.count())
        self.assertNotEqual(group.id, 1)
    

    def test_group_uniqueness(self):
        group = mixer.blend(
            Group, slug="Locke_Lab", description="A place where miracles happen"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Group.objects.create(slug="Locke_Lab")
        self.assertEqual(Group.objects.count(), 1)
