from unittest import mock
from unittest.mock import patch
from django.test import TestCase
from django_nextflow.models import Execution, ProcessExecution
from mixer.backend.django import mixer
from core.permissions import *
from core.models import User, UserGroupLink
from samples.models import Collection

class GroupsByUserTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.groups = [mixer.blend(Group) for _ in range(4)]
        mixer.blend(UserGroupLink, user=self.user, group=self.groups[0], permission=1)
        mixer.blend(UserGroupLink, user=self.user, group=self.groups[1], permission=2)
        mixer.blend(UserGroupLink, user=self.user, group=self.groups[2], permission=3)


    def test_can_get_groups_by_user_with_exact_match(self):
        self.assertEqual(set(get_groups_by_user(self.user, 1)), {self.groups[0]})
        self.assertEqual(set(get_groups_by_user(self.user, 2)), {self.groups[1]})
        self.assertEqual(set(get_groups_by_user(self.user, 3)), {self.groups[2]})


    def test_can_get_groups_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_groups_by_user(self.user, 1, exact=False)), set(self.groups[:3]))
        self.assertEqual(set(get_groups_by_user(self.user, 2, exact=False)), set(self.groups[1:3]))



class UsersByGroupTests(TestCase):

    def setUp(self):
        self.group = mixer.blend(Group)
        self.users = [mixer.blend(User) for _ in range(4)]
        mixer.blend(UserGroupLink, group=self.group, user=self.users[0], permission=1)
        mixer.blend(UserGroupLink, group=self.group, user=self.users[1], permission=2)
        mixer.blend(UserGroupLink, group=self.group, user=self.users[2], permission=3)


    def test_can_get_users_by_group_with_exact_match(self):
        self.assertEqual(set(get_users_by_group(self.group, 1)), {self.users[0]})
        self.assertEqual(set(get_users_by_group(self.group, 2)), {self.users[1]})
        self.assertEqual(set(get_users_by_group(self.group, 3)), {self.users[2]})


    def test_can_get_users_by_group_with_non_exact_match(self):
        self.assertEqual(set(get_users_by_group(self.group, 1, exact=False)), set(self.users[:3]))
        self.assertEqual(set(get_users_by_group(self.group, 2, exact=False)), set(self.users[1:3]))



class CollectionsByUserTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.collections = [mixer.blend(Collection) for _ in range(5)]
        mixer.blend(CollectionUserLink, user=self.user, collection=self.collections[0], permission=1)
        mixer.blend(CollectionUserLink, user=self.user, collection=self.collections[1], permission=2)
        mixer.blend(CollectionUserLink, user=self.user, collection=self.collections[2], permission=3)
        mixer.blend(CollectionUserLink, user=self.user, collection=self.collections[3], permission=4)

    
    def test_can_get_collections_by_user_with_exact_match(self):
        self.assertEqual(set(get_collections_by_user(self.user, 1)), {self.collections[0]})
        self.assertEqual(set(get_collections_by_user(self.user, 2)), {self.collections[1]})
        self.assertEqual(set(get_collections_by_user(self.user, 3)), {self.collections[2]})
        self.assertEqual(set(get_collections_by_user(self.user, 4)), {self.collections[3]})


    def test_can_get_collections_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_collections_by_user(self.user, 1, exact=False)), set(self.collections[:4]))
        self.assertEqual(set(get_collections_by_user(self.user, 2, exact=False)), set(self.collections[1:4]))
        self.assertEqual(set(get_collections_by_user(self.user, 3, exact=False)), set(self.collections[2:4]))



class UsersByCollectionTests(TestCase):

    def setUp(self):
        self.collection = mixer.blend(Collection)
        self.users = [mixer.blend(User) for _ in range(5)]
        mixer.blend(CollectionUserLink, collection=self.collection, user=self.users[0], permission=1)
        mixer.blend(CollectionUserLink, collection=self.collection, user=self.users[1], permission=2)
        mixer.blend(CollectionUserLink, collection=self.collection, user=self.users[2], permission=3)
        mixer.blend(CollectionUserLink, collection=self.collection, user=self.users[3], permission=4)
    

    def test_can_get_users_by_collection_with_exact_match(self):
        self.assertEqual(set(get_users_by_collection(self.collection, 1)), {self.users[0]})
        self.assertEqual(set(get_users_by_collection(self.collection, 2)), {self.users[1]})
        self.assertEqual(set(get_users_by_collection(self.collection, 3)), {self.users[2]})
        self.assertEqual(set(get_users_by_collection(self.collection, 4)), {self.users[3]})


    def test_can_get_users_by_collection_with_non_exact_match(self):
        self.assertEqual(set(get_users_by_collection(self.collection, 1, exact=False)), set(self.users[:4]))
        self.assertEqual(set(get_users_by_collection(self.collection, 2, exact=False)), set(self.users[1:4]))
        self.assertEqual(set(get_users_by_collection(self.collection, 3, exact=False)), set(self.users[2:4]))


    
class CollectionsByGroupTests(TestCase):

    def setUp(self):
        self.group = mixer.blend(Group)
        self.collections = [mixer.blend(Collection) for _ in range(4)]
        mixer.blend(CollectionGroupLink, group=self.group, collection=self.collections[0], permission=1)
        mixer.blend(CollectionGroupLink, group=self.group, collection=self.collections[1], permission=2)
        mixer.blend(CollectionGroupLink, group=self.group, collection=self.collections[2], permission=3)
    

    def test_can_get_collections_by_user_with_exact_match(self):
        self.assertEqual(set(get_collections_by_group(self.group, 1)), {self.collections[0]})
        self.assertEqual(set(get_collections_by_group(self.group, 2)), {self.collections[1]})
        self.assertEqual(set(get_collections_by_group(self.group, 3)), {self.collections[2]})


    def test_can_get_collections_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_collections_by_group(self.group, 1, exact=False)), set(self.collections[:3]))
        self.assertEqual(set(get_collections_by_group(self.group, 2, exact=False)), set(self.collections[1:3]))



class GroupsByCollectionTests(TestCase):

    def setUp(self):
        self.collection = mixer.blend(Collection)
        self.groups = [mixer.blend(Group) for _ in range(4)]
        mixer.blend(CollectionGroupLink, collection=self.collection, group=self.groups[0], permission=1)
        mixer.blend(CollectionGroupLink, collection=self.collection, group=self.groups[1], permission=2)
        mixer.blend(CollectionGroupLink, collection=self.collection, group=self.groups[2], permission=3)
    

    def test_can_get_groups_by_collection_with_exact_match(self):
        self.assertEqual(set(get_groups_by_collection(self.collection, 1)), {self.groups[0]})
        self.assertEqual(set(get_groups_by_collection(self.collection, 2)), {self.groups[1]})
        self.assertEqual(set(get_groups_by_collection(self.collection, 3)), {self.groups[2]})


    def test_can_get_groups_by_collection_with_non_exact_match(self):
        self.assertEqual(set(get_groups_by_collection(self.collection, 1, exact=False)), set(self.groups[:3]))
        self.assertEqual(set(get_groups_by_collection(self.collection, 2, exact=False)), set(self.groups[1:3]))



class SamplesByUserTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.samples = [mixer.blend(Sample) for _ in range(4)]
        mixer.blend(SampleUserLink, user=self.user, sample=self.samples[0], permission=1)
        mixer.blend(SampleUserLink, user=self.user, sample=self.samples[1], permission=2)
        mixer.blend(SampleUserLink, user=self.user, sample=self.samples[2], permission=3)
    

    def test_can_get_samples_by_user_with_exact_match(self):
        self.assertEqual(set(get_samples_by_user(self.user, 1)), {self.samples[0]})
        self.assertEqual(set(get_samples_by_user(self.user, 2)), {self.samples[1]})
        self.assertEqual(set(get_samples_by_user(self.user, 3)), {self.samples[2]})


    def test_can_get_samples_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_samples_by_user(self.user, 1, exact=False)), set(self.samples[:3]))
        self.assertEqual(set(get_samples_by_user(self.user, 2, exact=False)), set(self.samples[1:3]))
        self.assertEqual(set(get_samples_by_user(self.user, 3, exact=False)), set(self.samples[2:3]))



class UsersBySampleTests(TestCase):

    def setUp(self):
        self.sample = mixer.blend(Sample)
        self.users = [mixer.blend(User) for _ in range(4)]
        mixer.blend(SampleUserLink, sample=self.sample, user=self.users[0], permission=1)
        mixer.blend(SampleUserLink, sample=self.sample, user=self.users[1], permission=2)
        mixer.blend(SampleUserLink, sample=self.sample, user=self.users[2], permission=3)
    

    def test_can_get_users_by_sample_with_exact_match(self):
        self.assertEqual(set(get_users_by_sample(self.sample, 1)), {self.users[0]})
        self.assertEqual(set(get_users_by_sample(self.sample, 2)), {self.users[1]})
        self.assertEqual(set(get_users_by_sample(self.sample, 3)), {self.users[2]})


    def test_can_get_users_by_sample_with_non_exact_match(self):
        self.assertEqual(set(get_users_by_sample(self.sample, 1, exact=False)), set(self.users[:3]))
        self.assertEqual(set(get_users_by_sample(self.sample, 2, exact=False)), set(self.users[1:3]))



class JobsByUserTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.jobs = [mixer.blend(Job) for _ in range(5)]
        mixer.blend(JobUserLink, user=self.user, job=self.jobs[0], permission=1)
        mixer.blend(JobUserLink, user=self.user, job=self.jobs[1], permission=2)
        mixer.blend(JobUserLink, user=self.user, job=self.jobs[2], permission=3)
        mixer.blend(JobUserLink, user=self.user, job=self.jobs[3], permission=4)
    

    def test_can_get_jobs_by_user_with_exact_match(self):
        self.assertEqual(set(get_jobs_by_user(self.user, 1)), {self.jobs[0]})
        self.assertEqual(set(get_jobs_by_user(self.user, 2)), {self.jobs[1]})
        self.assertEqual(set(get_jobs_by_user(self.user, 3)), {self.jobs[2]})
        self.assertEqual(set(get_jobs_by_user(self.user, 4)), {self.jobs[3]})


    def test_can_get_jobs_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_jobs_by_user(self.user, 1, exact=False)), set(self.jobs[:4]))
        self.assertEqual(set(get_jobs_by_user(self.user, 2, exact=False)), set(self.jobs[1:4]))
        self.assertEqual(set(get_jobs_by_user(self.user, 3, exact=False)), set(self.jobs[2:4]))



class UsersByJobTest(TestCase):

    def setUp(self):
        self.job = mixer.blend(Job)
        self.users = [mixer.blend(User) for _ in range(5)]
        mixer.blend(JobUserLink, job=self.job, user=self.users[0], permission=1)
        mixer.blend(JobUserLink, job=self.job, user=self.users[1], permission=2)
        mixer.blend(JobUserLink, job=self.job, user=self.users[2], permission=3)
        mixer.blend(JobUserLink, job=self.job, user=self.users[3], permission=4)
    

    def test_can_get_users_by_job_with_exact_match(self):
        self.assertEqual(set(get_users_by_job(self.job, 1)), {self.users[0]})
        self.assertEqual(set(get_users_by_job(self.job, 2)), {self.users[1]})
        self.assertEqual(set(get_users_by_job(self.job, 3)), {self.users[2]})
        self.assertEqual(set(get_users_by_job(self.job, 4)), {self.users[3]})


    def test_can_get_users_by_job_with_non_exact_match(self):
        self.assertEqual(set(get_users_by_job(self.job, 1, exact=False)), set(self.users[:4]))
        self.assertEqual(set(get_users_by_job(self.job, 2, exact=False)), set(self.users[1:4]))
        self.assertEqual(set(get_users_by_job(self.job, 3, exact=False)), set(self.users[2:4]))



class DataByUserTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.data = [mixer.blend(Data) for _ in range(4)]
        mixer.blend(DataUserLink, user=self.user, data=self.data[0], permission=1)
        mixer.blend(DataUserLink, user=self.user, data=self.data[1], permission=2)
        mixer.blend(DataUserLink, user=self.user, data=self.data[2], permission=3)
        mixer.blend(DataUserLink, user=self.user, data=self.data[3], permission=4)
    

    def test_can_get_data_by_user_with_exact_match(self):
        self.assertEqual(set(get_data_by_user(self.user, 1)), {self.data[0]})
        self.assertEqual(set(get_data_by_user(self.user, 2)), {self.data[1]})
        self.assertEqual(set(get_data_by_user(self.user, 3)), {self.data[2]})
        self.assertEqual(set(get_data_by_user(self.user, 4)), {self.data[3]})


    def test_can_get_data_by_user_with_non_exact_match(self):
        self.assertEqual(set(get_data_by_user(self.user, 1, exact=False)), set(self.data[:4]))
        self.assertEqual(set(get_data_by_user(self.user, 2, exact=False)), set(self.data[1:4]))
        self.assertEqual(set(get_data_by_user(self.user, 3, exact=False)), set(self.data[2:4]))



class UsersByDataTest(TestCase):

    def setUp(self):
        self.data = mixer.blend(Data)
        self.users = [mixer.blend(User) for _ in range(4)]
        mixer.blend(DataUserLink, data=self.data, user=self.users[0], permission=1)
        mixer.blend(DataUserLink, data=self.data, user=self.users[1], permission=2)
        mixer.blend(DataUserLink, data=self.data, user=self.users[2], permission=3)
        mixer.blend(DataUserLink, data=self.data, user=self.users[3], permission=4)
    

    def test_can_get_users_by_data_with_exact_match(self):
        self.assertEqual(set(get_users_by_data(self.data, 1)), {self.users[0]})
        self.assertEqual(set(get_users_by_data(self.data, 2)), {self.users[1]})
        self.assertEqual(set(get_users_by_data(self.data, 3)), {self.users[2]})
        self.assertEqual(set(get_users_by_data(self.data, 4)), {self.users[3]})


    def test_can_get_users_by_data_with_non_exact_match(self):
        self.assertEqual(set(get_users_by_data(self.data, 1, exact=False)), set(self.users[:4]))
        self.assertEqual(set(get_users_by_data(self.data, 2, exact=False)), set(self.users[1:4]))
        self.assertEqual(set(get_users_by_data(self.data, 3, exact=False)), set(self.users[2:4]))



class UserPermissionsOnCollectionTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.collection = mixer.blend(Collection)
        self.patch1 = patch("core.permissions.get_groups_by_user")
        self.mock_groups = self.patch1.start()
        self.mock_groups.return_value = []


    def tearDown(self):
        self.patch1.stop()


    def test_no_link(self):
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 1))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 2))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 3))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 4))
    

    def test_public_collections_always_readable(self):
        self.collection.private = False
        self.collection.save()
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 1))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 2))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 3))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 4))
    

    def test_can_access_direct_link(self):
        link = mixer.blend(CollectionUserLink, user=self.user, collection=self.collection, permission=1)
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 1))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 2))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 3))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 4))
        link.permission = 3
        link.save()
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 1))
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 2))
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 3))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 4))
    

    def test_can_access_group_link(self):
        group1 = mixer.blend(Group)
        group2 = mixer.blend(Group)
        group3 = mixer.blend(Group)
        self.mock_groups.return_value = [group1, group2, group3]
        mixer.blend(CollectionGroupLink, group=group1, collection=self.collection, permission=1)
        mixer.blend(CollectionGroupLink, group=group2, collection=self.collection, permission=2)
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 1))
        self.assertTrue(does_user_have_permission_on_collection(self.user, self.collection, 2))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 3))
        self.assertFalse(does_user_have_permission_on_collection(self.user, self.collection, 4))
        self.mock_groups.assert_called_with(self.user, permission=2, exact=False)



class UserPermissionsOnSampleTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.sample = mixer.blend(Sample, collection=None)
        self.patch1 = patch("core.permissions.does_user_have_permission_on_collection")
        self.mock_perm = self.patch1.start()
        self.mock_perm.return_value = False


    def tearDown(self):
        self.patch1.stop()
    

    def test_no_link(self):
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 1))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 2))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 3))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 4))
    

    def test_public_samples_always_readable(self):
        self.sample.private = False
        self.sample.save()
        self.assertTrue(does_user_have_permission_on_sample(self.user, self.sample, 1))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 2))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 3))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 4))
    

    def test_can_access_direct_link(self):
        link = mixer.blend(SampleUserLink, user=self.user, sample=self.sample, permission=1)
        self.assertTrue(does_user_have_permission_on_sample(self.user, self.sample, 1))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 2))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 3))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 4))
        link.permission = 3
        link.save()
        self.assertTrue(does_user_have_permission_on_sample(self.user, self.sample, 1))
        self.assertTrue(does_user_have_permission_on_sample(self.user, self.sample, 2))
        self.assertTrue(does_user_have_permission_on_sample(self.user, self.sample, 3))
        self.assertFalse(does_user_have_permission_on_sample(self.user, self.sample, 4))


    def test_can_get_permission_via_collection(self):
        self.sample.collection = mixer.blend(Collection)
        self.assertIs(
            does_user_have_permission_on_sample(self.user, self.sample, 2),
            self.mock_perm.return_value
        )
        self.mock_perm.assert_called_with(self.user, self.sample.collection, 2)



class UserPermissionsOnJobTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.job = mixer.blend(Job, collection=None, sample=None)
        self.patch1 = patch("core.permissions.does_user_have_permission_on_collection")
        self.mock_cperm = self.patch1.start()
        self.mock_cperm.return_value = False
        self.patch2 = patch("core.permissions.does_user_have_permission_on_sample")
        self.mock_sperm = self.patch2.start()
        self.mock_sperm.return_value = False


    def tearDown(self):
        self.patch1.stop()
        self.patch2.stop()
    

    def test_no_link(self):
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 1))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 2))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 3))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 4))
    

    def test_public_jobs_always_readable(self):
        self.job.private = False
        self.job.save()
        self.assertTrue(does_user_have_permission_on_job(self.user, self.job, 1))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 2))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 3))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 4))
    

    def test_can_access_direct_link(self):
        link = mixer.blend(JobUserLink, user=self.user, job=self.job, permission=1)
        self.assertTrue(does_user_have_permission_on_job(self.user, self.job, 1))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 2))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 3))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 4))
        link.permission = 3
        link.save()
        self.assertTrue(does_user_have_permission_on_job(self.user, self.job, 1))
        self.assertTrue(does_user_have_permission_on_job(self.user, self.job, 2))
        self.assertTrue(does_user_have_permission_on_job(self.user, self.job, 3))
        self.assertFalse(does_user_have_permission_on_job(self.user, self.job, 4))


    def test_can_get_permission_via_collection(self):
        self.job.collection = mixer.blend(Collection)
        self.job.save()
        self.assertIs(
            does_user_have_permission_on_job(self.user, self.job, 2),
            self.mock_cperm.return_value
        )
        self.mock_cperm.assert_called_with(self.user, self.job.collection, 2)
    

    def test_can_get_permission_via_sample(self):
        self.job.sample = mixer.blend(Sample)
        self.job.save()
        self.assertIs(
            does_user_have_permission_on_job(self.user, self.job, 2),
            self.mock_sperm.return_value
        )
        self.mock_sperm.assert_called_with(self.user, self.job.sample, 2)



class UserPermissionsOnDataTests(TestCase):

    def setUp(self):
        self.user = mixer.blend(User)
        self.data = mixer.blend(Data, upstream_process_execution=None)
        self.link = mixer.blend(DataLink, data=self.data, collection=None)
        self.patch1 = patch("core.permissions.does_user_have_permission_on_collection")
        self.mock_cperm = self.patch1.start()
        self.mock_cperm.return_value = False
        self.patch2 = patch("core.permissions.does_user_have_permission_on_sample")
        self.mock_sperm = self.patch2.start()
        self.mock_sperm.return_value = False
        self.patch3 = patch("core.permissions.does_user_have_permission_on_job")
        self.mock_jperm = self.patch3.start()
        self.mock_jperm.return_value = False


    def tearDown(self):
        self.patch1.stop()
        self.patch2.stop()
        self.patch3.stop()
    

    def test_no_link(self):
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 1))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 2))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 3))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 4))
    

    def test_public_data_always_readable(self):
        self.link.private = False
        self.link.save()
        self.assertTrue(does_user_have_permission_on_data(self.user, self.data, 1))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 2))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 3))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 4))
    

    def test_can_access_direct_link(self):
        link = mixer.blend(DataUserLink, user=self.user, data=self.data, permission=1)
        self.assertTrue(does_user_have_permission_on_data(self.user, self.data, 1))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 2))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 3))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 4))
        link.permission = 3
        link.save()
        self.assertTrue(does_user_have_permission_on_data(self.user, self.data, 1))
        self.assertTrue(does_user_have_permission_on_data(self.user, self.data, 2))
        self.assertTrue(does_user_have_permission_on_data(self.user, self.data, 3))
        self.assertFalse(does_user_have_permission_on_data(self.user, self.data, 4))


    def test_can_get_permission_via_collection(self):
        self.link.collection = mixer.blend(Collection)
        self.link.save()
        self.assertIs(
            does_user_have_permission_on_data(self.user, self.data, 2),
            self.mock_cperm.return_value
        )
        self.mock_cperm.assert_called_with(self.user, self.link.collection, 2)
    

    def test_can_get_permission_via_job(self):
        job = mixer.blend(Job)
        execution = mixer.blend(Execution, job=job)
        process_execution = mixer.blend(ProcessExecution, execution=execution)
        self.data.upstream_process_execution = process_execution
        self.data.save()
        self.assertIs(
            does_user_have_permission_on_data(self.user, self.data, 2),
            self.mock_jperm.return_value
        )
        self.mock_jperm.assert_called_with(self.user, job, 2)



class ReadableCollectionsTests(TestCase):

    def test_can_get_public(self):
        c1 = mixer.blend(Collection, private=False)
        c2 = mixer.blend(Collection, private=False)
        mixer.blend(Collection)
        self.assertEqual(set(readable_collections(Collection.objects.all())), {c1, c2})
    

    def test_can_get_via_links(self):
        user = mixer.blend(User)
        c1 = mixer.blend(Collection, private=False) # public
        c2 = mixer.blend(Collection) # user has link
        mixer.blend(CollectionUserLink, user=user, collection=c2)
        c3 = mixer.blend(Collection) # group has link
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, collection=c3, group=group)
        c4 = mixer.blend(Collection) # link to other user
        mixer.blend(CollectionUserLink, collection=c4)
        c5 = mixer.blend(Collection) # link to other group
        mixer.blend(CollectionGroupLink, collection=c5)
        self.assertEqual(
            set(readable_collections(Collection.objects.all(), user)), {c1, c2, c3}
        )



class ReadableSamplesTests(TestCase):

    def test_can_get_public(self):
        s1 = mixer.blend(Sample, private=False)
        s2 = mixer.blend(Sample, private=False)
        mixer.blend(Sample)
        self.assertEqual(set(readable_samples(Sample.objects.all())), {s1, s2})
    

    def test_can_get_via_links(self):
        user = mixer.blend(User)
        s1 = mixer.blend(Sample, private=False) # public
        s2 = mixer.blend(Sample) # user has link
        mixer.blend(SampleUserLink, user=user, sample=s2)
        s3 = mixer.blend(Sample, collection=mixer.blend(Collection)) # user has link to collection
        mixer.blend(CollectionUserLink, user=user, collection=s3.collection)
        s4 = mixer.blend(Sample) # group has link to collection
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, collection=s4.collection, group=group)
        s5 = mixer.blend(Sample) # link to other user
        mixer.blend(SampleUserLink, sample=s5)
        self.assertEqual(
            set(readable_samples(Sample.objects.all(), user)), {s1, s2, s3, s4}
        )



class ReadableJobsTests(TestCase):

    def test_can_get_public(self):
        j1 = mixer.blend(Job, private=False)
        j2 = mixer.blend(Job, private=False)
        mixer.blend(Job)
        self.assertEqual(set(readable_jobs(Job.objects.all())), {j1, j2})
    

    def test_can_get_via_links(self):
        user = mixer.blend(User)
        j1 = mixer.blend(Job, private=False) # public
        j2 = mixer.blend(Job) # user has link
        mixer.blend(JobUserLink, user=user, job=j2)
        j3 = mixer.blend(Job, sample=mixer.blend(Sample)) # user has link to sample
        mixer.blend(SampleUserLink, user=user, sample=j3.sample)
        j4 = mixer.blend(Job, collection=mixer.blend(Collection)) # user has link to collection
        mixer.blend(CollectionUserLink, user=user, collection=j4.collection)
        j5 = mixer.blend(Job, sample=mixer.blend(Sample, collection=mixer.blend(Collection))) # user has link to sample collection
        mixer.blend(CollectionUserLink, user=user, collection=j5.sample.collection)
        j6 = mixer.blend(Job) # group has link to collection
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, collection=j6.collection, group=group)
        j7 = mixer.blend(Job, sample=mixer.blend(Sample, collection=mixer.blend(Collection))) # group has link to sample collection
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, collection=j7.sample.collection, group=group)
        j8 = mixer.blend(Job) # link to other user
        mixer.blend(JobUserLink, job=j8)
        self.assertEqual(
            set(readable_jobs(Job.objects.all(), user)), {j1, j2, j3, j4, j5, j6, j7}
        )



class ReadableDataTests(TestCase):
    
    def test_can_get_public(self):
        d1 = mixer.blend(Data)
        mixer.blend(DataLink, data=d1, private=False)
        d2 = mixer.blend(Data)
        mixer.blend(DataLink, data=d2, private=False)
        mixer.blend(Data)
        self.assertEqual(set(readable_data(Data.objects.all())), {d1, d2})
    

    def test_can_get_via_links(self):
        user = mixer.blend(User)

        d1 = mixer.blend(Data, filename="d1") # public
        mixer.blend(DataLink, data=d1, private=False)
        
        d2 = mixer.blend(Data, filename="d2") # user has link
        mixer.blend(DataUserLink, user=user, data=d2)

        # user has link to job
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution)
        d3 = mixer.blend(
            Data, filename="d3", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        mixer.blend(JobUserLink, user=user, job=job)
        
        # user has link to job's sample
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution)
        d4 = mixer.blend(
            Data, filename="d4", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        mixer.blend(SampleUserLink, user=user, sample=job.sample)
        
        # user has link to collection
        d5 = mixer.blend(Data, filename="d5") 
        mixer.blend(DataLink, data=d5)
        mixer.blend(CollectionUserLink, user=user, collection=d5.link.collection)
        
        # user has link to job's collection
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution)
        d6 = mixer.blend(
            Data, filename="d6", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        mixer.blend(CollectionUserLink, user=user, collection=job.collection)
        
        # user has link to job's sample's collection
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution)
        d7 = mixer.blend(
            Data, filename="d7", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        mixer.blend(CollectionUserLink, user=user, collection=d7.upstream_process_execution.execution.job.sample.collection)
        
        # group has link to collection
        d8 = mixer.blend(Data, filename="d8") 
        mixer.blend(DataLink, data=d8)
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, group=group, collection=d8.link.collection)
        
        # group has link to job's collection
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution, collection=mixer.blend(Collection))
        d9 = mixer.blend(
            Data, filename="d9", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, group=group, collection=job.collection)
        
        # group has link to job's sample's collection
        execution = mixer.blend(Execution, identifier="xxx")
        job = mixer.blend(Job, execution=execution)
        d10 = mixer.blend(
            Data, filename="d10", upstream_process_execution=mixer.blend(
                ProcessExecution, execution=execution, name="prex"
            )
        )
        group = mixer.blend(Group)
        mixer.blend(UserGroupLink, user=user, group=group)
        mixer.blend(CollectionGroupLink, group=group, collection=job.sample.collection)
        
        d11 = mixer.blend(Data, filename="d11") # link to other user
        mixer.blend(DataUserLink, data=d11)
        
        self.assertEqual(
            set(readable_data(Data.objects.all(), user)), {d1, d2, d3, d4, d5, d6, d7, d8, d9, d10}
        )