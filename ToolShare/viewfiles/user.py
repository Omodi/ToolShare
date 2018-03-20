from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.models import User
from ToolShare.models import Shed, Notification, ToolTransaction

from ToolShare.decorators import object_required, sharezone_required, check_reservations

@login_required
@check_reservations
def dashboard(request):
    """ Displays dashboard with notifications, owned tool and borrowed tools if any """
    message = request.session["temp_message"] if "temp_message" in request.session else None
    message_class = request.session["message_class"] if "message_class" in request.session else None
    request.session["temp_message"] = None
    request.session["message_class"] = None
    context = {
        "user": request.user,
        "tools": request.user.tools.all(),
        "sheds": request.user.my_sheds.all(),
        "toolsBorrowed": request.user.profile.borrowedTools(),
        "message": message,
        "message_class": message_class
    }
    return render(request, "ToolShare/pages/dashboard.html", context)


@login_required
def notificationList(request):
    return HttpResponse("A list of notifications.")


@login_required
@object_required(class_object=Notification, key="nid")
def deleteNotification(request, nid):
    note = get_object_or_404(Notification, pk=nid)

    if note.user==request.user:
        note.delete()

    return redirect(request.GET["next"] if "next" in request.GET else "ToolShare:Dashboard")


@login_required
def relevantShed(request):
    """ List of sheds in shareZones """
    error = ""
    sheds = []
    zone = request.user.profile.zone
    allSheds = list(Shed.objects.filter(zone=zone))
    for i in range(len(allSheds)):
        if allSheds[i].searchable:
            sheds.append(allSheds[i])
        elif request.user in allSheds[i].user_list.all():
            sheds.append(allSheds[i])


    if len(sheds) == 0:
        error = "No Community Sheds found"
    context = {
        "sheds": sheds,
        "error": error
    }
    return render(request, "ToolShare/pages/mySheds.html", context)

from django.contrib.contenttypes.models import ContentTypeManager

@login_required
@object_required(class_object=User, key="uid", allow_none=True)
@sharezone_required(class_object=User, key="uid", allow_none=True)
def userProfile(request, uid=None):
    """ Profile page with name and address.  Link to change account information if your own profile.  Also includes list of tool """
    if not uid:
        uid = request.user.id
    profileUser = User.objects.get(pk=uid)
    toolsToShow = []
    for obj in profileUser.tools.all():
        if isinstance(obj.currentShareLocation(), Shed) and obj.currentShareLocation().invite_only and profileUser!=request.user:
            continue
        else:
            toolsToShow.append(obj)
    
    context = {
        "profileUser": profileUser,
        "tools": toolsToShow,
        "sheds": request.user.my_sheds.all(),
        "transactions": ToolTransaction.objects.filter(object_id = profileUser.id, object_type=ContentTypeManager().get_for_model(model=User) ).exclude(tool__owner__id = profileUser.id),
        "rating": User.objects.filter(id=uid)[0].profile.getRating(),
        "user":request.user
    }
    return render(request, "ToolShare/pages/userProfile.html", context)


@login_required
def editUserProfile(request):
    """ Sets a new name and address """
    error = None
    if request.POST:
        name = request.POST["name"]
        address = request.POST["address"]
        method = request.POST["method"]
        if not name:
            error = "Please enter a name."
        else:
            request.user.profile.name = name
            request.user.profile.address = address
            request.user.profile.method = method
            request.user.profile.save()
            return redirect("ToolShare:UserProfile")
    context = {
        "error": error
    }
    return render(request, "ToolShare/pages/editUserProfile.html", context);