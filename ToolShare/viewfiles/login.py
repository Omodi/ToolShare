from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import authenticate, login as djangoLogin, logout as djangoLogout
from django.contrib.auth.models import User

from ToolShare.models import Profile, ShareZone

# from django.http import HttpResponse


def register(request):
    """ registers a user with information from the template """
    error = ""
    name = ""
    email = ""
    zipcode = ""

    if request.POST:
        name = request.POST["name"]
        email = request.POST["email"]
        zipcode = request.POST["zipcode"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        if not name or not email or not zipcode or not password or not password2:
            error = "Please fill out all fields."
        elif password != password2:
            error = "Passwords do not match."
        elif len(zipcode) != 5 or not zipcode.isdigit():
            error = "Zipcode is not valid."
        else:
            numUsers = User.objects.filter(username=email).count()
            userExists = numUsers >= 1
            if userExists:
                error = "User already exists."
            else:
                zones = ShareZone.objects.filter(zipcode=zipcode)
                zone = None
                if (len(zones) >= 1):
                    zone = zones[0]
                else:
                    zone = ShareZone(zipcode=zipcode)
                    zone.save()
                user = User.objects.create_user(email, password=password)
                profile = Profile(zone=zone, name=name, user=user)
                profile.save()
                if user:
                    user.backend = "django.contrib.auth.backends.ModelBackend"
                    djangoLogin(request, user)
                    return redirect("ToolShare:Dashboard")
                else:
                    error = "Failed to create user."

    context = {
        "error": error,
        "name": name,
        "email": email,
        "zipcode": zipcode,
        "debug": str(bool(request.POST))
    }
    return render(request, "ToolShare/pages/register.html", context)


def login(request):
    """ authenticates the user by email and password.  Redirects user to dashboard  """
    error = ""
    success = ""
    email = ""

    if "next" in request.GET:
        error = "Please log in to continue."

    if request.POST:
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(username=email, password=password)
        if user:
            if user.is_active:
                djangoLogin(request, user)
                return redirect("ToolShare:Dashboard")
            else:
                error = "This account is disabled."
        else:
            error = "Invalid login."

    context = {
        "error": error,
        "success": success,
        "email": email
    }
    return render(request, "ToolShare/pages/login.html", context)



def logout(request):
    """ logsout user and returns them to landingpage """
    djangoLogout(request)
    return redirect("ToolShare:LandingPoint")