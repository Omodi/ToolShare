from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.core.urlresolvers import reverse

from ToolShare.models import Tool, ToolTransaction, Tag, Shed, Reservation
from ToolShare.decorators import object_required, sharezone_required, check_reservations

from django.template.defaultfilters import slugify

import datetime


@login_required
def toolRegistration(request):
    """ Registers a tool with information from template """
    name = ""
    description = ""
    tags = ""
    error = ""
    success = ""
    if request.POST:
        name = request.POST["name"]
        description = request.POST["description"]
        tags = request.POST["tags"]
        if not name or not description:
            error = "Please fill out all fields"
        elif len(slugify(name)) <= 0:
            error = "Invalid name."
        else:
            tool = request.user.profile.addTool(name, desc=description, tags=tags)
            if tool:
                success = "Tool registered successfully! If you would like to share it right away, mark it as available!"
                return redirect('ToolShare:IndividualToolDetail', toolId=tool.pk)

    context = {
        "name": name,
        "description": description,
        "tags": tags,
        "error": error,
        "success": success,
        "debug": str(bool(request.POST))
    }
    return render(request, "ToolShare/pages/toolRegister.html", context)


@login_required
@object_required(class_object=Tool, key="toolId")
@check_reservations
def deleteTool(request, toolId):
    """ Removes tool from database and from user """
    error = None
    success = None
    
    tool = get_object_or_404(Tool, pk=toolId)
    if tool.owner==request.user:
        name = tool.name
        tool.delete()
        success = "Tool '%s' successfully removed." % name
    else:
        error = "You don't have access to delete that tool."

    request.session["temp_message"] = error if error else success
    
    return redirect("ToolShare:Dashboard")

@login_required
@object_required(class_object=Tool, key="toolId")
@object_required(class_object=Shed, key="shedId")
@sharezone_required(class_object=Tool, key="toolId")
@sharezone_required(class_object=Shed, key="shedId")
@check_reservations
def moveToolToShed(request, toolId, shedId):
    """ Change currentShareLocation to selected shed """
    error = None
    success = None

    tool = get_object_or_404(Tool, pk=toolId)
    shed = get_object_or_404(Shed, pk=shedId)

    if request.user==tool.owner and shed.zone==request.user.profile.zone \
        and tool.currentShareLocation()==tool.owner and tool.currentHolder()==tool.owner:
        tool.movedTo(shed)
        success = "Tool successfully moved into shed %s" % shed.name
    else:
        error = "You don't have the right permissions to move a tool like that."

    if error:
        request.session["temp_message"] = error
        return redirect("ToolShare:Dashboard")
    else:
        return redirect("ToolShare:CommunityShedToolListandProfile", shedId=shedId)

@login_required
@object_required(class_object=Tool, key="toolId")
@object_required(class_object=Shed, key="shedId")
@sharezone_required(class_object=Tool, key="toolId")
@sharezone_required(class_object=Shed, key="shedId")
@check_reservations
def moveToolToOwner(request, toolId, shedId):
    """ Return tool currentShareLocation to owner """
    error = None
    success = None

    tool = get_object_or_404(Tool, pk=toolId)
    shed = get_object_or_404(Shed, pk=shedId)

    # Shed coordinators and tool owners should be able to move tools back to their owner

    if (request.user==tool.owner or request.user==shed.coordinator) \
        and tool.currentShareLocation()==shed and tool.currentHolder()==shed:
        tool.movedTo(tool.owner)
        success = "Tool %s successfully moved back to its owner." % toolId
    else:
        error = "You don't have the right permissions to move a tool like that."
    
    if error:
        request.session["temp_message"] = error
        return redirect("ToolShare:Dashboard")
    else:
        return redirect("ToolShare:IndividualToolDetail", toolId=toolId)

@login_required
@object_required(class_object=Tool, key="toolId")
@sharezone_required(class_object=Tool, key="toolId")
@check_reservations
def toolBorrowRequest(request, toolId):
    """ Creates notification to borrow tool. """
    tool = get_object_or_404(Tool, pk=toolId)

    success = None

    startDate = request.POST["startDate"] if "startDate" in request.POST else None
    endDate = request.POST["endDate"] if "endDate" in request.POST else None

    if startDate and not endDate:
        endDate = startDate

    if not (startDate and endDate):
        return redirect("ToolShare:Dashboard")

    startd = startDate.split("/")
    endd = endDate.split("/")

    startDate = startd[2]+"-"+startd[0]+"-"+startd[1]
    endDate = endd[2]+"-"+endd[0]+"-"+endd[1]

    if Reservation.objects.filter(tool=tool, start_date__range=[startDate, endDate]).count()>0 or Reservation.objects.filter(tool=tool, end_date__range=[startDate, endDate]).count()>0:
        return redirect("ToolShare:Dashboard") # Reservation attempted to be in invalid range

    if tool.owner == request.user:
        reservation = Reservation(start_date=startDate, end_date=endDate, tool=tool, user=None, finalized=True)
        reservation.save()
        return redirect("ToolShare:Dashboard") # no reserving your own tool, blackout date instead


    if isinstance(tool.currentShareLocation(), User):
        reservation = Reservation(start_date=startDate, end_date=endDate, tool=tool, user=request.user)
        reservation.save()
        tool.owner.profile.notify("%s would like to borrow your tool '%s'. Would you like to approve him or her?" % \
            (request.user.profile.name, tool.name), reverse("ToolShare:ApproveLend", \
            kwargs={'rid': reservation.id}))
        success = "%s has been notified that you would like to borrow his tool, check back later to see if they've approved your reservation." % \
            (tool.owner.profile.name)

    else:
        reservation = Reservation(start_date=startDate, end_date=endDate, tool=tool, user=request.user, finalized=True)
        reservation.save()
        success = "You successfully reserved '%s' from %s." % \
            (tool.name, tool.currentHolder().name)

    request.session["temp_message"] = success
    request.session["message_class"] = "success"

    return redirect("ToolShare:Dashboard")

@login_required
@object_required(class_object=Reservation, key="rid")
@check_reservations
def toolApproveLend(request, rid):
    """ Moves tool to sharer """
    error = ""
    success = ""

    reservation = get_object_or_404(Reservation, pk=rid)
    if reservation.tool.owner == request.user:
        reservation.finalized = True
        reservation.save()

        request.session["temp_message"] = "You have approved a reservation."
        request.session["message_class"] = "success"
        
        reservation.user.profile.notify("%s has approved your request to borrow '%s'." % \
            (request.user.profile.name, reservation.tool.name))
    else:
        request.session["temp_message"] = "You cannot approve that reservation."
        request.session["message_class"] = "warning"

    return redirect("ToolShare:Dashboard")

@login_required
@object_required(class_object=Tool, key="toolId")
@sharezone_required(class_object=Tool, key="toolId")
@check_reservations
def toolReturn(request, toolId):
    """ Returns tool to currentShareLocation """
    tool = get_object_or_404(Tool, pk=toolId)

    if tool.currentHolder()==request.user: 
        tool.movedTo(tool.currentShareLocation())

    return redirect("ToolShare:Dashboard")


@login_required
@check_reservations
def toolSearchResults(request):
    """ Returns a list of tools with matching tags in sharezone.  If there are no tags return a tools in sharezone """
    results = ""
    success = ""
    error = ""
    listName = 'Search Results'

    query = request.GET["q"] if "q" in request.GET else ""

    valid_tags = []
    for c in query.split(" "):
        localtag = None
        try:
            localtag = Tag.objects.get(slug=slugify(c))
        except:
            continue
        valid_tags += [localtag]

    results = Tool.objects.filter(tags__in=valid_tags)

    if query=="":
        results = request.user.profile.zone.getAllAvailableTools()

    for tool in results:
        share_location = tool.currentShareLocation()
        if isinstance(share_location, Shed):
            if share_location.user_list.count() != 0 and not request.user in share_location.user_list.all():
                results = results.exclude(id=tool.id)
    if results.count() == 0:
        error = "No tools found."
    elif query:
        success = str(results.count()) + " results found."
    context = {
        "tools": results,
        "success": success,
        "error": error,
        "listname": listName,
        "q": query
    }
    return render(request, "ToolShare/pages/searchResults.html", context )


@login_required
@object_required(class_object=Tool, key="toolId")
@sharezone_required(class_object=Tool, key="toolId")
@check_reservations
def toolDetail(request, toolId):
    """ Renders tool detail page """
    this_tool =  get_object_or_404(Tool, pk=toolId)

    loc = this_tool.currentShareLocation()

    initial_date = datetime.date.today()

    tool_reservations = Reservation.objects.filter(tool=this_tool, finalized=True, end_date__gt=(initial_date + datetime.timedelta(1))).order_by("start_date")

    for r in tool_reservations:
        if r.start_date <= initial_date and r.end_date >= initial_date:
            initial_date = r.end_date + datetime.timedelta(1)
        elif r.start_date > initial_date:
            break

    context = {
        "tool":  this_tool,
        "available": this_tool.isAvailable(),
        "curLoc": loc,
        "tool_reservations": tool_reservations,
        "initial_date": "{}/{}/{}".format(initial_date.month, initial_date.day, initial_date.year)
    }
    return render(request, "ToolShare/pages/tool_info.html", context)