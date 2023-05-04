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
    if not data or data.filename != name:
        raise Http404
    actual_name = f"{name}.zip" if data.is_directory else name
    actual_full_path = f"{data.full_path}.zip" if data.is_directory else data.full_path
    response = HttpResponse()
    response["Content-Disposition"] = "attachment; filename={0}".format(actual_name)
    if settings.SERVE_FILES:
        with open(actual_full_path, "rb") as f:
            response.content = f.read()
    else:
        response["X-Accel-Redirect"] = f"/internal{actual_full_path}"
    return response