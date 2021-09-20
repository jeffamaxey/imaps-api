from unittest import mock
from unittest.mock import patch
from django.test import TestCase
from mixer.backend.django import mixer
from core.permissions import *
from core.models import User, UserGroupLink
from samples.models import Collection

class PermissionTest(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.group = mixer.blend(Group)
        self.collection = mixer.blend(Collection)
        self.sample = mixer.blend(Sample, collection=None)
        self.execution = mixer.blend(Execution, collection=None, sample=None)



class CollectionOwnerRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(is_user_owner_of_collection(self.user, self.collection))
    

    def test_check_fails_when_insufficient_link(self):
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=3)
        self.assertFalse(is_user_owner_of_collection(self.user, self.collection))
    

    def test_check_passes_when_owner(self):
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=4)
        self.assertTrue(is_user_owner_of_collection(self.user, self.collection))



class CollectionShareRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_share_collection(self.user, self.collection))
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_fails_when_insufficient_user_link(self, mock_groups):
        mock_groups.return_value = []
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=2)
        self.assertFalse(can_user_share_collection(self.user, self.collection))
        mock_groups.assert_called_with(self.user)
    

    def test_check_passes_with_user_share_link(self):
        link = CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=3)
        self.assertTrue(can_user_share_collection(self.user, self.collection))
        link.permission = 4
        link.save()
        self.assertTrue(can_user_share_collection(self.user, self.collection))
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_fails_when_insufficient_group_link(self, mock_groups):
        mock_groups.return_value = [self.group]
        CollectionGroupLink.objects.create(group=self.group, collection=self.collection, permission=2)
        self.assertFalse(can_user_share_collection(self.user, self.collection))
        mock_groups.assert_called_with(self.user)
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_passes_with_group_share_link(self, mock_groups):
        mock_groups.return_value = [self.group]
        UserGroupLink.objects.create(user=self.user, group=self.group, permission=2)
        CollectionGroupLink.objects.create(group=self.group, collection=self.collection, permission=3)
        self.assertTrue(can_user_share_collection(self.user, self.collection))



class CollectionEditRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_edit_collection(self.user, self.collection))
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_fails_when_insufficient_user_link(self, mock_groups):
        mock_groups.return_value = []
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=1)
        self.assertFalse(can_user_edit_collection(self.user, self.collection))
        mock_groups.assert_called_with(self.user)
    

    def test_check_passes_with_user_share_link(self):
        link = CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=2)
        self.assertTrue(can_user_edit_collection(self.user, self.collection))
        link.permission = 3
        link.save()
        self.assertTrue(can_user_edit_collection(self.user, self.collection))
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_fails_when_insufficient_group_link(self, mock_groups):
        mock_groups.return_value = [self.group]
        CollectionGroupLink.objects.create(group=self.group, collection=self.collection, permission=1)
        self.assertFalse(can_user_edit_collection(self.user, self.collection))
        mock_groups.assert_called_with(self.user)
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_passes_with_group_share_link(self, mock_groups):
        mock_groups.return_value = [self.group]
        CollectionGroupLink.objects.create(group=self.group, collection=self.collection, permission=2)
        self.assertTrue(can_user_edit_collection(self.user, self.collection))



class CollectionViewRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_view_collection(self.user, self.collection))
    

    def test_check_passes_with_user_share_link(self):
        link = CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=1)
        self.assertTrue(can_user_view_collection(self.user, self.collection))
        link.permission = 2
        link.save()
        self.assertTrue(can_user_view_collection(self.user, self.collection))
    

    @patch("core.permissions.groups_with_user_as_member")
    def test_check_passes_with_group_share_link(self, mock_groups):
        mock_groups.return_value = [self.group]
        CollectionGroupLink.objects.create(group=self.group, collection=self.collection, permission=1)
        self.assertTrue(can_user_view_collection(self.user, self.collection))
    

    def test_check_passes_when_public(self):
        self.collection.private = False
        self.collection.save()
        self.assertTrue(can_user_view_collection(None, self.collection))



class SampleOwnerRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(is_user_owner_of_sample(self.user, self.sample))
    

    def test_check_fails_when_with_max_sample_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=3)
        self.assertFalse(is_user_owner_of_sample(self.user, self.sample))
    

    def test_check_fails_when_with_no_collection_link(self):
        self.sample.collection = self.collection
        self.sample.save()
        self.assertFalse(is_user_owner_of_sample(self.user, self.sample))
    

    def test_check_fails_when_with_insufficient_collection_link(self):
        self.sample.collection = self.collection
        self.sample.save()
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=3)
        self.assertFalse(is_user_owner_of_sample(self.user, self.sample))
    

    def test_check_passes_when_with_sufficient_collection_link(self):
        self.sample.collection = self.collection
        self.sample.save()
        CollectionUserLink.objects.create(user=self.user, collection=self.collection, permission=4)
        self.assertTrue(is_user_owner_of_sample(self.user, self.sample))



class SampleShareRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_share_sample(self.user, self.sample))
    

    def test_check_fails_when_insufficient_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=2)
        self.assertFalse(can_user_share_sample(self.user, self.sample))
    

    def test_check_passes_when_sufficient_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=3)
        self.assertTrue(can_user_share_sample(self.user, self.sample))
    

    @patch("core.permissions.can_user_share_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.sample.collection = self.collection
        self.sample.save()
        self.assertEqual(can_user_share_sample(self.user, self.sample), "result")
        mock_can.assert_called_with(self.user, self.collection)



class SampleEditRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_edit_sample(self.user, self.sample))
    

    def test_check_fails_when_insufficient_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=1)
        self.assertFalse(can_user_edit_sample(self.user, self.sample))
    

    def test_check_passes_when_sufficient_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=2)
        self.assertTrue(can_user_edit_sample(self.user, self.sample))
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=3)
        self.assertTrue(can_user_edit_sample(self.user, self.sample))
    

    @patch("core.permissions.can_user_edit_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.sample.collection = self.collection
        self.sample.save()
        self.assertEqual(can_user_edit_sample(self.user, self.sample), "result")
        mock_can.assert_called_with(self.user, self.collection)



class SampleViewRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_view_sample(self.user, self.sample))
    

    def test_check_passes_when_sufficient_link(self):
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=1)
        self.assertTrue(can_user_view_sample(self.user, self.sample))
        SampleUserLink.objects.create(user=self.user, sample=self.sample, permission=3)
        self.assertTrue(can_user_view_sample(self.user, self.sample))
    

    @patch("core.permissions.can_user_view_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.sample.collection = self.collection
        self.sample.save()
        self.assertEqual(can_user_view_sample(self.user, self.sample), "result")
        mock_can.assert_called_with(self.user, self.collection)
    

    def test_check_passes_when_public(self):
        self.sample.private = False
        self.sample.save()
        self.assertTrue(can_user_view_sample(None, self.sample))



class ExecutionOwnerRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(is_user_owner_of_execution(self.user, self.execution))
    

    def test_check_fails_with_insufficient_execution_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=3)
        self.assertFalse(is_user_owner_of_execution(self.user, self.execution))
    

    def test_check_passes_with_sufficient_execution_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=4)
        self.assertTrue(is_user_owner_of_execution(self.user, self.execution))
    

    @patch("core.permissions.is_user_owner_of_collection")
    def test_check_uses_collection_ownership(self, mock_is):
        mock_is.return_value = "result"
        self.execution.collection = self.collection
        self.execution.sample = self.sample
        self.execution.save()
        self.assertEqual(is_user_owner_of_execution(self.user, self.execution), "result")
        mock_is.assert_called_with(self.user, self.collection)
    

    @patch("core.permissions.is_user_owner_of_sample")
    def test_check_uses_collection_ownership(self, mock_is):
        mock_is.return_value = "result"
        self.execution.sample = self.sample
        self.execution.save()
        self.assertEqual(is_user_owner_of_execution(self.user, self.execution), "result")
        mock_is.assert_called_with(self.user, self.sample)



class ExecutionShareRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_share_execution(self.user, self.execution))
    

    def test_check_fails_when_insufficient_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=2)
        self.assertFalse(can_user_share_execution(self.user, self.execution))
    

    def test_check_passes_when_sufficient_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=3)
        self.assertTrue(can_user_share_execution(self.user, self.execution))
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=4)
        self.assertTrue(can_user_share_execution(self.user, self.execution))
    

    @patch("core.permissions.can_user_share_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.collection = self.collection
        self.execution.save()
        self.assertEqual(can_user_share_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.collection)
    

    @patch("core.permissions.can_user_share_sample")
    def test_check_can_use_sample_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.sample = self.sample
        self.execution.save()
        self.assertEqual(can_user_share_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.sample)



class ExecutionEditRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_edit_execution(self.user, self.execution))
    

    def test_check_fails_when_insufficient_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=1)
        self.assertFalse(can_user_edit_execution(self.user, self.execution))
    

    def test_check_passes_when_sufficient_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=2)
        self.assertTrue(can_user_edit_execution(self.user, self.execution))
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=4)
        self.assertTrue(can_user_edit_execution(self.user, self.execution))
    

    @patch("core.permissions.can_user_edit_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.collection = self.collection
        self.execution.save()
        self.assertEqual(can_user_edit_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.collection)
    

    @patch("core.permissions.can_user_edit_sample")
    def test_check_can_use_sample_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.sample = self.sample
        self.execution.save()
        self.assertEqual(can_user_edit_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.sample)



class ExecutionViewRightsCheckTests(PermissionTest):

    def test_check_fails_when_no_link(self):
        self.assertFalse(can_user_view_execution(self.user, self.execution))
    

    def test_check_passes_when_sufficient_link(self):
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=1)
        self.assertTrue(can_user_view_execution(self.user, self.execution))
        ExecutionUserLink.objects.create(user=self.user, execution=self.execution, permission=4)
        self.assertTrue(can_user_view_execution(self.user, self.execution))
    

    @patch("core.permissions.can_user_view_collection")
    def test_check_can_use_collection_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.collection = self.collection
        self.execution.save()
        self.assertEqual(can_user_view_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.collection)
    

    @patch("core.permissions.can_user_view_sample")
    def test_check_can_use_sample_check(self, mock_can):
        mock_can.return_value = "result"
        self.execution.sample = self.sample
        self.execution.save()
        self.assertEqual(can_user_view_execution(self.user, self.execution), "result")
        mock_can.assert_called_with(self.user, self.sample)
    

    def test_check_passes_when_public(self):
        self.execution.private = False
        self.execution.save()
        self.assertTrue(can_user_view_execution(None, self.execution))



class ReadableCollectionsTests(TestCase):

    def test_can_filter_collections(self):
        user = mixer.blend(User)
        mixer.blend(Collection)
        public = mixer.blend(Collection, private=False)
        owned = mixer.blend(Collection)
        CollectionUserLink.objects.create(collection=owned, user=user, permission=4)
        readable = mixer.blend(Collection)
        CollectionUserLink.objects.create(collection=readable, user=user, permission=1)
        group_readable = mixer.blend(Collection)
        group = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=group_readable, group=group, permission=1)
        collections = Collection.objects.all()
        self.assertEqual(collections.count(), 5)
        with self.assertNumQueries(1):
            filtered = readable_collections(Collection.objects.all(), user)
        self.assertEqual(filtered.count(), 4)
        for col in [public, owned, readable, group_readable]:
            self.assertIn(col, filtered)
    

    def test_can_filter_samples(self):
        user = mixer.blend(User)
        mixer.blend(Sample)
        public = mixer.blend(Sample, private=False)
        readable = mixer.blend(Sample)
        SampleUserLink.objects.create(sample=readable, user=user, permission=1)
        collection_readable = mixer.blend(Sample)
        CollectionUserLink.objects.create(collection=collection_readable.collection, user=user, permission=1)
        group_readable = mixer.blend(Sample)
        group = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=group_readable.collection, group=group, permission=1)
        samples = Sample.objects.all()
        self.assertEqual(samples.count(), 5)
        with self.assertNumQueries(1):
            filtered = readable_samples(Sample.objects.all(), user)
        self.assertEqual(filtered.count(), 4)
        for col in [public, readable, collection_readable, group_readable]:
            self.assertIn(col, filtered)
    

    def test_can_filter_executions(self):
        user = mixer.blend(User)
        mixer.blend(Execution)
        public = mixer.blend(Execution, private=False)
        readable = mixer.blend(Execution)
        ExecutionUserLink.objects.create(execution=readable, user=user, permission=1)
        collection_readable = mixer.blend(Execution, collection=mixer.blend(Collection))
        CollectionUserLink.objects.create(collection=collection_readable.collection, user=user, permission=1)
        sample_readable = mixer.blend(Execution, sample=mixer.blend(Sample))
        SampleUserLink.objects.create(sample=sample_readable.sample, user=user, permission=1)
        sample_collection_readable = mixer.blend(Execution, sample=mixer.blend(Sample))
        CollectionUserLink.objects.create(collection=sample_collection_readable.sample.collection, user=user, permission=1)
        group_readable1 = mixer.blend(Execution, collection=mixer.blend(Collection))
        group = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=group_readable1.collection, group=group, permission=1)
        group_readable2 = mixer.blend(Execution, sample=mixer.blend(Sample))
        group = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group, permission=2)
        CollectionGroupLink.objects.create(collection=group_readable2.sample.collection, group=group, permission=1)
        executions = Execution.objects.all()
        self.assertEqual(executions.count(), 8)
        with self.assertNumQueries(1):
            filtered = readable_executions(Execution.objects.all(), user)
        self.assertEqual(filtered.count(), 7)
        for col in [public, readable, collection_readable, sample_readable, sample_collection_readable, group_readable1, group_readable2]:
            self.assertIn(col, filtered)



class GroupsRunByUserTests(TestCase):

    def test_can_get_groups_run_by_user(self):
        user = mixer.blend(User)
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group1, permission=3)
        UserGroupLink.objects.create(user=user, group=group2, permission=2)
        UserGroupLink.objects.create(user=mixer.blend(User), group=group3, permission=3)
        self.assertEqual(list(groups_run_by_user(user)), [group1])
    


class GroupsWithUserAsMember(TestCase):

    def test_can_get_groups_with_user_as_member(self):
        user = mixer.blend(User)
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        group4 = mixer.blend(Group)
        UserGroupLink.objects.create(user=user, group=group1, permission=3)
        UserGroupLink.objects.create(user=user, group=group2, permission=2)
        UserGroupLink.objects.create(user=user, group=group3, permission=1)
        UserGroupLink.objects.create(user=mixer.blend(User), group=group4, permission=2)
        self.assertEqual(list(groups_with_user_as_member(user)), [group1, group2])



class GroupAdminsTests(TestCase):

    def test_can_get_group_admins(self):
        group = mixer.blend(Group)
        user1 = mixer.blend(User)
        user2 = mixer.blend(User)
        user3 = mixer.blend(User)
        UserGroupLink.objects.create(user=user1, group=group, permission=3)
        UserGroupLink.objects.create(user=user2, group=group, permission=2)
        UserGroupLink.objects.create(user=user3, group=mixer.blend(Group), permission=3)
        self.assertEqual(list(group_admins(group)), [user1])



class GroupMembersTests(TestCase):

    def test_can_get_group_members(self):
        group = mixer.blend(Group)
        user1 = mixer.blend(User)
        user2 = mixer.blend(User)
        user3 = mixer.blend(User)
        user4 = mixer.blend(User)
        UserGroupLink.objects.create(user=user1, group=group, permission=3)
        UserGroupLink.objects.create(user=user2, group=group, permission=2)
        UserGroupLink.objects.create(user=user3, group=group, permission=1)
        UserGroupLink.objects.create(user=user4, group=mixer.blend(Group), permission=2)
        self.assertEqual(list(group_members(group)), [user1, user2])



class CollectionsOwnedByUserTests(TestCase):

    def test_can_get_collections_owned_by_user(self):
        user = mixer.blend(User)
        collection1 = mixer.blend(Collection)
        collection2 = mixer.blend(Collection)
        collection3 = mixer.blend(Collection)
        CollectionUserLink.objects.create(user=user, collection=collection1, permission=4)
        CollectionUserLink.objects.create(user=user, collection=collection2, permission=3)
        CollectionUserLink.objects.create(user=mixer.blend(User), collection=collection3, permission=4)
        self.assertEqual(list(collections_owned_by_user(user)), [collection1])



class CollectionOwnersTests(TestCase):

    def test_can_get_collection_owners(self):
        collection = mixer.blend(Collection)
        user1 = mixer.blend(User)
        user2 = mixer.blend(User)
        user3 = mixer.blend(User)
        CollectionUserLink.objects.create(user=user1, collection=collection, permission=4)
        CollectionUserLink.objects.create(user=user2, collection=collection, permission=3)
        CollectionUserLink.objects.create(user=user3, collection=mixer.blend(Collection), permission=4)
        self.assertEqual(list(collection_owners(collection)), [user1])



class ExecutionsOwnedByUserTests(TestCase):

    def test_can_get_executions_owned_by_user(self):
        user = mixer.blend(User)
        execution1 = mixer.blend(Execution)
        execution2 = mixer.blend(Execution)
        execution3 = mixer.blend(Execution)
        ExecutionUserLink.objects.create(user=user, execution=execution1, permission=4)
        ExecutionUserLink.objects.create(user=user, execution=execution2, permission=3)
        ExecutionUserLink.objects.create(user=mixer.blend(User), execution=execution3, permission=4)
        self.assertEqual(list(executions_owned_by_user(user)), [execution1])



class ExecutionOwnersTests(TestCase):

    def test_can_get_execution_owners(self):
        execution = mixer.blend(Execution)
        user1 = mixer.blend(User)
        user2 = mixer.blend(User)
        user3 = mixer.blend(User)
        ExecutionUserLink.objects.create(user=user1, execution=execution, permission=4)
        ExecutionUserLink.objects.create(user=user2, execution=execution, permission=3)
        ExecutionUserLink.objects.create(user=user3, execution=mixer.blend(Execution), permission=4)
        self.assertEqual(list(execution_owners(execution)), [user1])