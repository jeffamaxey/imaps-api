import jwt
import time
from mixer.backend.django import mixer
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db import transaction
from django.conf import settings
from core.models import User, Group, GroupInvitation

class GroupInvitationCreationTests(TestCase):

    def test_can_create_group_invitation(self):
        user, group = mixer.blend(User, name="jack"), mixer.blend(Group, name="others")
        invitation = GroupInvitation.objects.create(user=user, group=group)
        self.assertEqual(str(invitation), "others invitation to jack")
        self.assertLess(abs(time.time() - invitation.creation_time), 1)
        self.assertNotEqual(invitation.id, 1)
    

    def test_editing_invitation_doesnt_change_creation_time(self):
        user, group = mixer.blend(User), mixer.blend(Group)
        invitation = mixer.blend(GroupInvitation, user=user, group=group, creation_time=10000)
        invitation.user = mixer.blend(User)
        invitation.save()
        self.assertEqual(invitation.creation_time, 10000)
    


class GroupInvitationOrderingTests(TestCase):

    def test_group_invitations_ordered_by_creation_time(self):
        invitation1 = mixer.blend(GroupInvitation, id=2)
        invitation2 = mixer.blend(GroupInvitation, id=1)
        invitation3 = mixer.blend(GroupInvitation, id=3)
        self.assertEqual(list(GroupInvitation.objects.all()), [invitation1, invitation2, invitation3])