from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ToolShare.models import Shed
from ToolShare.decorators import object_required, sharezone_required

@login_required
@sharezone_required(class_object=Shed, key="shedId")
@object_required(class_object=Shed, key="shedId")
def shedPreferences(request, shedId):
    """ given data in request, modifies the given shed. """
    shed = Shed.objects.filter(id=shedId)[0]
    name = shed.name
    address = shed.address
    zipcode = ""
    privateSettings = ""
    error = ""
    success = ""
    if request.user == shed.coordinator:
        if request.POST:
            name = request.POST["name"]
            address = request.POST["address"]
            if not name or not address:
                error = "Please fill out all fields."
            else:
                shed.name = name
                shed.address = address
                privateSettings = request.POST["privateSettings"] if "privateSettings" in request.POST else ["-1"]
                if privateSettings[0] == "1":
                    shed.searchable = True
                elif privateSettings[0] == "2":
                    shed.searchable = False
                shed.save()
                success = "Shed changed successfully!"
                return redirect("ToolShare:CommunityShedToolListandProfile", shedId=shed.pk)
    else:
        return redirect("ToolShare:Dashboard")

    context = {
        "error": error,
        "success": success,
        "name": name,
        "address": address,
        "zipcode": zipcode,
        "invite_only": shed.invite_only,
        "privateSettings": privateSettings,
        "searchable": shed.searchable,
        "debug": str(bool(request.POST))
    }
    return render(request, "ToolShare/pages/shedPreferences.html", context)

@login_required
def relevantShedSelection(request, toolId):
    """ Displays all sheds in shareZone and let you move tool(from toolId) to selected shed """
    error = ""
    zone = request.user.profile.zone
    sheds = []
    allSheds = list(zone.getAllSheds())
    for i in range(len(allSheds)):
        if allSheds[i].searchable:
            sheds.append(allSheds[i])
        elif request.user in allSheds[i].user_list.all():
            sheds.append(allSheds[i])
    if len(sheds) == 0:
        error = "No Community Sheds found"
    context = {
        "sheds": sheds,
        "error": error,
        "toolId": toolId
    }
    return render(request, "ToolShare/pages/move_to_shed.html", context)  

@login_required
@object_required(class_object=Shed, key="shedId")
@sharezone_required(class_object=Shed, key="shedId")
def shedProfile(request, shedId):
    """ Displays shed name, address and tool list """
    error = ""
    users = []
    shed = list(Shed.objects.filter(id=shedId))
    if len(shed) == 0:
        error = "No Community Shed found"
        context = {
            "name": "",
            "address": "",
            "zipcode": "",
            "users": users,
            "error": error
        }
    else:
        tools = []
        allTools = request.user.profile.zone.getAllAvailableTools()
        for tool in allTools:
            if tool.currentShareLocation() == shed[0]:
                tools.append(tool)
        if shed[0].user_list:
            users = shed[0].user_list.all()
        context = {
            "name": shed[0].name,
            "address": shed[0].address,
            "zipcode": shed[0].zone.zipcode,
            "tools": tools,
            "users": users,
            "invite_only": shed[0].invite_only,
            "membership": request.user in shed[0].user_list.all(),
            "shedId": shed[0].id,
            "coordinator": shed[0].coordinator,
            "error": error
        }
    return render(request, "ToolShare/pages/shedProfile.html", context)

@login_required
def shedRegistration(request):
    """ Creates a shed and adds it to the shareZone.  shed arguments obtained from template """
    name = ""
    address = ""
    zipcode = ""
    privateSettings = ""
    error = ""
    success = ""

    if request.POST:
        name = request.POST["name"]
        address = request.POST["address"]
        if not name or not address:
            error = "Please fill out all fields."
        else:
            shed = Shed(name=name, coordinator=request.user, zone=request.user.profile.zone, address=address, invite_only=True)
            shed.save()
            privateSettings = request.POST["privateSettings"]
            if privateSettings[0] == '0':
                shed.invite_only = False
                shed.searchable = True
            elif privateSettings[0] == '1':
                shed.invite_only = True
                shed.searchable = True
                shed.user_list.add(request.user)
            elif privateSettings[0] == '2':
                shed.invite_only = True
                shed.searchable = False
                shed.user_list.add(request.user)
            shed.save()
            success = "Shed created successfully!"
            return redirect("ToolShare:CommunityShedToolListandProfile", shedId=shed.pk)

    context = {
        "error": error,
        "success": success,
        "name": name,
        "address": address,
        "zipcode": zipcode,
        "privateSettings": privateSettings,
        "debug": str(bool(request.POST))
    }
    return render(request, "ToolShare/pages/ShedRegistration.html", context)

@login_required
@object_required(class_object=Shed, key="shedId")
@sharezone_required(class_object=Shed, key="shedId")
def requestToJoin(request, shedId):
    """ Sends a notification to the shed coordinator to join the shed"""
    shed = Shed.objects.filter(id=shedId)[0]
    shed.coordinator.profile.notify("%s wants to join %s." % 
     (request.user.profile.name, shed.name), reverse("ToolShare:AddUserToShed", kwargs={'shedId': shed.id, 'uId': request.user.id}), "Accept", "Deny")

    request.session["temp_message"] = "%s has been notified of your request to join their Shed." % (shed.coordinator.profile.name)
    request.session["message_class"] = "success"

    return redirect("ToolShare:Dashboard")

@login_required
@object_required(class_object=Shed, key="shedId")
@object_required(class_object=User, key="uId")
@sharezone_required(class_object=Shed, key="shedId")
@sharezone_required(class_object=User, key="uId")
def addUserToShed(request, shedId, uId):
    """ adds the user (by uId) to the shed (by shedId) """
    shed = Shed.objects.filter(id=shedId)[0]
    user = User.objects.filter(id=uId)[0]
    if shed.coordinator.id == request.user.id:
        shed.user_list.add(user)
    return redirect("ToolShare:Dashboard")