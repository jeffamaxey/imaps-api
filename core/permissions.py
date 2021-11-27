"""Functions for filtering objects by permission state. There are three kinds of
function here:

1. Functions for getting objects which have a direct permission relationship
with another, by permission level. This ignores indirect permissions (user
permissions via groups).

2. Functions for checking if a particular should have a given level of access on
an object, after looking at all possible links they might have to it.

3. Functions for filtering a queryset by those a user can know about."""

from core.models import User, Group
from analysis.models import Collection, CollectionGroupLink, CollectionUserLink, Sample, SampleUserLink, Job, JobUserLink, Data, DataUserLink, DataLink
from django.db.models import Q
from django_nextflow.models import Data

def get_groups_by_user(user, permission, exact=True):
    """Gets all groups which have a link with a particular user, matching a
    given permission."""

    permssion_arg = f"usergrouplink__permission"
    if not exact: permssion_arg += "__gte"
    return Group.objects.filter(**{
        "usergrouplink__user": user, permssion_arg: permission
    })


def get_users_by_group(group, permission, exact=True):
    """Gets all users which have a link with a particular group, matching a
    given permission."""

    permssion_arg = f"usergrouplink__permission"
    if not exact: permssion_arg += "__gte"
    return User.objects.filter(**{
        "usergrouplink__group": group, permssion_arg: permission
    })


def get_collections_by_user(user, permission, exact=True):
    """Gets all collections which have a direct link with a particular user,
    matching a given permission."""

    permssion_arg = f"collectionuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return Collection.objects.filter(**{
        "collectionuserlink__user": user, permssion_arg: permission
    })


def get_users_by_collection(collection, permission, exact=True):
    """Gets all users which have a direct link with a particular collection,
    matching a given permission."""

    permssion_arg = f"collectionuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return User.objects.filter(**{
        "collectionuserlink__collection": collection, permssion_arg: permission
    })


def get_collections_by_group(group, permission, exact=True):
    """Gets all collections which have a link with a particular group, matching
    a given permission."""

    permssion_arg = f"collectiongrouplink__permission"
    if not exact: permssion_arg += "__gte"
    return Collection.objects.filter(**{
        "collectiongrouplink__group": group, permssion_arg: permission
    })


def get_groups_by_collection(collection, permission, exact=True):
    """Gets all groups which have a link with a particular collection, matching
    a given permission."""

    permssion_arg = f"collectiongrouplink__permission"
    if not exact: permssion_arg += "__gte"
    return Group.objects.filter(**{
        "collectiongrouplink__collection": collection, permssion_arg: permission
    })


def get_samples_by_user(user, permission, exact=True):
    """Gets all samples which have a link with a particular user, matching a
    given permission."""

    permssion_arg = f"sampleuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return Sample.objects.filter(**{
        "sampleuserlink__user": user, permssion_arg: permission
    })


def get_users_by_sample(sample, permission, exact=True):
    """Gets all users which have a link with a particular sample, matching a
    given permission."""

    permssion_arg = f"sampleuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return User.objects.filter(**{
        "sampleuserlink__sample": sample, permssion_arg: permission
    })


def get_jobs_by_user(user, permission, exact=True):
    """Gets all jobs which have a link with a particular user, matching a
    given permission."""

    permssion_arg = f"jobuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return Job.objects.filter(**{
        "jobuserlink__user": user, permssion_arg: permission
    })


def get_users_by_job(job, permission, exact=True):
    """Gets all users which have a link with a particular job, matching a
    given permission."""

    permssion_arg = f"jobuserlink__permission"
    if not exact: permssion_arg += "__gte"
    return User.objects.filter(**{
        "jobuserlink__job": job, permssion_arg: permission
    })


def get_data_by_user(user, permission, exact=True):
    """Gets all data files which have a link with a particular user, matching a
    given permission."""

    permssion_arg = f"datauserlink__permission"
    if not exact: permssion_arg += "__gte"
    return Data.objects.filter(**{
        "datauserlink__user": user, permssion_arg: permission
    })


def get_users_by_data(data, permission, exact=True):
    """Gets all users which have a link with a particular data file, matching a
    given permission."""

    permssion_arg = f"datauserlink__permission"
    if not exact: permssion_arg += "__gte"
    return User.objects.filter(**{
        "datauserlink__data": data, permssion_arg: permission
    })




def does_user_have_permission_on_collection(user, collection, permission):
    """Checks whether a user has a particular permission (or higher) on a
    collection. The direct links will be checked, as well as links via
    groups."""

    if permission == 1 and not collection.private: return True
    if CollectionUserLink.objects.filter(
        collection=collection, user=user, permission__gte=permission
    ).count() > 0: return True
    for group in get_groups_by_user(user, permission=2, exact=False):
        if CollectionGroupLink.objects.filter(
            collection=collection, group=group, permission__gte=permission
        ).count() > 0: return True
    return False


def does_user_have_permission_on_sample(user, sample, permission):
    """Checks whether a user has a particular permission (or higher) on a
    sample. The direct links will be checked, as well as links via the parent
    collection (if one exists)."""

    if permission == 1 and not sample.private: return True
    if SampleUserLink.objects.filter(
        sample=sample, user=user, permission__gte=permission
    ).count() > 0: return True
    if sample.collection:
        return does_user_have_permission_on_collection(
            user, sample.collection, permission
        )
    return False


def does_user_have_permission_on_job(user, job, permission):
    """Checks whether a user has a particular permission (or higher) on a
    job. The direct links will be checked, as well as links via the parent
    collection or sample (if they exists)."""

    if permission == 1 and not job.private: return True
    if JobUserLink.objects.filter(
        job=job, user=user, permission__gte=permission
    ).count() > 0: return True
    if job.collection:
        return does_user_have_permission_on_collection(user, job.collection, permission)
    if job.sample:
        return does_user_have_permission_on_sample(user, job.sample, permission)
    return False


def does_user_have_permission_on_data(user, data, permission):
    """Checks whether a user has a particular permission (or higher) on a
    data file. The direct links will be checked, as well as links via the parent
    collection, sample or job (if they exists)."""

    link = DataLink.objects.get(data=data)
    if permission == 1 and not link.private: return True
    if DataUserLink.objects.filter(
        data=data, user=user, permission__gte=permission
    ).count() > 0: return True
    if link.collection:
        return does_user_have_permission_on_collection(user, link.collection, permission)
    if data.upstream_process_execution:
        return does_user_have_permission_on_job(
            user, data.upstream_process_execution.execution.job, permission
        )
    return False




def readable_collections(queryset, user=None):
    """Takes a Collection queryset and filters it by those a particular user is
    allowed to know exist and read."""

    if user:
        return queryset.filter(
            Q(private=False) |\
            Q(users=user) |\
            Q(groups__users=user)
        )
    else:
        return queryset.filter(private=False)


def readable_samples(queryset, user=None):
    """Takes a Sample queryset and filters it by those a particular user is
    allowed to know exist and read."""

    if user:
        return queryset.filter(
            Q(private=False) |\
            Q(users=user) |\
            Q(collection__users=user) |\
            Q(collection__groups__users=user)
        )
    else:
        return queryset.filter(private=False)


def readable_jobs(queryset, user=None):
    """Takes a Job queryset and filters it by those a particular user is
    allowed to know exist and read."""

    if user:
        return queryset.filter(
            Q(private=False) |\
            Q(users=user) |\
            Q(sample__users=user) |\
            Q(collection__users=user) |\
            Q(sample__collection__users=user) |\
            Q(collection__groups__users=user) |\
            Q(sample__collection__groups__users=user)
        )
    else:
        return queryset.filter(private=False)


def readable_data(queryset, user=None):
    """Takes a Data queryset and filters it by those a particular user is
    allowed to know exist and read."""

    if user:
        return queryset.filter(
            Q(link__private=False) |\
            Q(datauserlink__user=user) |\
            Q(upstream_process_execution__execution__job__users=user) |\
            Q(upstream_process_execution__execution__job__sample__users=user) |\
            Q(upstream_process_execution__execution__job__sample__collection__users=user) |\
            Q(upstream_process_execution__execution__job__collection__users=user) |\
            Q(link__collection__users=user) |\
            Q(link__collection__groups__users=user) |\
            Q(upstream_process_execution__execution__job__collection__groups__users=user) |\
            Q(upstream_process_execution__execution__job__sample__collection__groups__users=user)
        )
    else:
        return queryset.filter(link__private=False)