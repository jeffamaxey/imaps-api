"""The functions in this module are for (1) determining what rights a user
should have on a particular object, (2) filtering a queryset of objects by those
a user should be able to see/know about, (3) returning the objects that some
other object has a particular permission relationship with."""

from core.models import User, Group
from samples.models import Collection, CollectionGroupLink, CollectionUserLink, Sample, SampleUserLink, Job, JobUserLink
from django_nextflow.models import Data

def is_user_owner_of_collection(user, collection):
    """Checks whether a user is the owner of a collection."""

    return CollectionUserLink.objects.filter(
        collection=collection, user=user, permission=4
    ).count() > 0


def can_user_share_collection(user, collection):
    """Checks whether a user is permitted to share a collection."""

    if CollectionUserLink.objects.filter(
        collection=collection, user=user, permission__gte=3
    ).count() > 0: return True
    for group in groups_with_user_as_member(user):
        if CollectionGroupLink.objects.filter(
            collection=collection, group=group, permission__gte=3
        ).count() > 0: return True
    return False


def can_user_edit_collection(user, collection):
    """Checks whether a user is permitted to edit a collection."""

    if CollectionUserLink.objects.filter(
        collection=collection, user=user, permission__gte=2
    ).count() > 0: return True
    for group in groups_with_user_as_member(user):
        if CollectionGroupLink.objects.filter(
            collection=collection, group=group, permission__gte=2
        ).count() > 0: return True
    return False


def can_user_view_collection(user, collection):
    """Checks whether a user is permitted to view a collection."""

    if collection.private == False: return True
    if CollectionUserLink.objects.filter(
        collection=collection, user=user, permission__gte=1
    ).count() > 0: return True
    for group in groups_with_user_as_member(user):
        if CollectionGroupLink.objects.filter(
            collection=collection, group=group, permission__gte=1
        ).count() > 0: return True
    return False


def is_user_owner_of_sample(user, sample):
    """Checks whether a user has ownership rights on a sample."""

    return bool(sample.collection) and CollectionUserLink.objects.filter(
        collection=sample.collection, user=user, permission=4
    ).count() > 0


def can_user_share_sample(user, sample):
    """Checks whether a user is permitted to share a sample."""

    if SampleUserLink.objects.filter(
        sample=sample, user=user, permission__gte=3
    ).count() > 0: return True
    if sample.collection: return can_user_share_collection(user, sample.collection)
    return False


def can_user_edit_sample(user, sample):
    """Checks whether a user is permitted to edit a sample."""

    if SampleUserLink.objects.filter(
        sample=sample, user=user, permission__gte=2
    ).count() > 0: return True
    if sample.collection: return can_user_edit_collection(user, sample.collection)
    return False


def can_user_view_sample(user, sample):
    """Checks whether a user is permitted to view a sample."""

    if sample.private == False: return True
    if SampleUserLink.objects.filter(
        sample=sample, user=user, permission__gte=1
    ).count() > 0: return True
    if sample.collection: return can_user_view_collection(user, sample.collection)
    return False


def is_user_owner_of_job(user, job):
    """Checks whether a user has ownership rights on an job."""

    if JobUserLink.objects.filter(
        job=job, user=user, permission__gte=4
    ).count() > 0: return True
    if job.collection: return is_user_owner_of_collection(user, job.collection)
    if job.sample: return is_user_owner_of_sample(user, job.sample)
    return False


def can_user_share_job(user, job):
    """Checks whether a user is permitted to share an job."""

    if JobUserLink.objects.filter(
        job=job, user=user, permission__gte=3
    ).count() > 0: return True
    if job.collection: return can_user_share_collection(user, job.collection)
    if job.sample: return can_user_share_sample(user, job.sample)
    return False


def can_user_edit_job(user, job):
    """Checks whether a user is permitted to edit an job."""

    if JobUserLink.objects.filter(
        job=job, user=user, permission__gte=2
    ).count() > 0: return True
    if job.collection: return can_user_edit_collection(user, job.collection)
    if job.sample: return can_user_edit_sample(user, job.sample)
    return False


def can_user_view_job(user, job):
    """Checks whether a user is permitted to view an job."""

    if job.private == False: return True
    if JobUserLink.objects.filter(
        job=job, user=user, permission__gte=1
    ).count() > 0: return True
    if job.collection: return can_user_view_collection(user, job.collection)
    if job.sample: return can_user_view_sample(user, job.sample)
    return False


def readable_collections(queryset, user):
    """Takes a Collection queryset and filters it by those a particular user is
    allowed to know exist and read."""

    viewable = queryset.filter(private=False)
    if user:
        viewable |= queryset.filter(users=user)
        for group in user.groups.all():
            viewable |= queryset.filter(groups=group)
    return viewable.all().distinct()


def readable_samples(queryset, user):
    """Takes a Sample queryset and filters it by those a particular user is
    allowed to know exist and read."""

    viewable = queryset.filter(private=False)
    if user:
        viewable |= queryset.filter(users=user)
        viewable |= queryset.filter(collection__users=user)
        for group in user.groups.all():
            viewable |= queryset.filter(collection__groups=group)
    return viewable.all().distinct()


def readable_jobs(queryset, user):
    """Takes an Job queryset and filters it by those a particular user is
    allowed to know exist and read."""

    viewable = queryset.filter(private=False)
    if user:
        viewable |= queryset.filter(users=user)
        viewable |= queryset.filter(sample__users=user)
        viewable |= queryset.filter(collection__users=user)
        viewable |= queryset.filter(sample__collection__users=user)
        for group in user.groups.all():
            viewable |= queryset.filter(collection__groups=group)
            viewable |= queryset.filter(sample__collection__groups=group)
    return viewable.all().distinct()


def groups_run_by_user(user):
    """Returns the groups that a user has admin rights over."""

    return Group.objects.filter(usergrouplink__user=user, usergrouplink__permission=3)


def groups_with_user_as_member(user):
    """Returns the groups that a user is a member of."""

    return Group.objects.filter(usergrouplink__user=user, usergrouplink__permission__gte=2)


def group_admins(group):
    """Returns the users which run a group."""

    return User.objects.filter(usergrouplink__group=group, usergrouplink__permission=3)


def group_members(group):
    """Returns the members of a group."""

    return User.objects.filter(usergrouplink__group=group, usergrouplink__permission__gte=2)


def collections_owned_by_user(user):
    """Returns the collections which a user owns."""

    return Collection.objects.filter(collectionuserlink__user=user, collectionuserlink__permission=4)


def collection_owners(collection):
    """Returns a collection's owners."""

    return User.objects.filter(collectionuserlink__collection=collection, collectionuserlink__permission=4)


def jobs_owned_by_user(user):
    """Returns the jobs which a user owns directly."""

    return Job.objects.filter(jobuserlink__user=user, jobuserlink__permission=4)


def job_owners(job):
    """Returns an job's direct owners."""

    return User.objects.filter(jobuserlink__job=job, jobuserlink__permission=4)


def data_owned_by_user(user):
    """Returns the data which a user owns."""

    return Data.objects.filter(datauserlink__user=user, datauserlink__permission=4)