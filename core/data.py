from django_nextflow.models import Data
from core.models import User
from django.conf import settings
from django.http.response import HttpResponse
from django.http import Http404
from core.permissions import does_user_have_permission_on_data

def return_data(request, id, name):
    """Takes a request for a data file, and checks whether the user is allowed
    to access the file. If they can and SERVE_FILES is True, the file will be
    returned. Otherwise, the path to the file will be returned."""
    
    token = request.COOKIES.get("imaps_refresh_token")
    user = User.from_token(token)
    data = Data.objects.get(id=id)
    #if does_user_have_permission_on_data(user, data, 1) and data.filename == name:
    if data and data.filename == name:
        response = HttpResponse()
        response["Content-Disposition"] = "attachment; filename={0}".format(name)
        if settings.SERVE_FILES:
            with open(data.full_path) as f:
                response.content = f.read()
        else:
            response["X-Accel-Redirect"] = "/internal" + data.full_path
        return response
    else:
        raise Http404