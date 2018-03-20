from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from ToolShare.models import Profile, ShareZone, Tool, ToolTransaction, Shed
from django.db.models import Sum, Count
from django.contrib.auth.models import User


def landingPoint(request):
    """ if user is not logged in display landingPage otherwise display Dashboard """
    if request.user.is_authenticated():
        return redirect("ToolShare:Dashboard")
    return render(request, "ToolShare/pages/landingPage.html")

@login_required    
def statistics(request):
    """ aggregates some community statistics, displays stats page"""
    users = Profile.objects.all().filter(zone__zipcode=request.user.profile.zone.zipcode).count()
    sharers = User.objects.filter(profile__zone__zipcode=request.user.profile.zone.zipcode).filter(tools__isnull=False).distinct().count()
    context = {
        "user_count": users,
        "with_count": sharers,
        "user_ratio": sharers/users * 100,
        "inverted_ratio": (1-(sharers/users)) * 100,
        "shed_count": Shed.objects.filter(zone__zipcode=request.user.profile.zone.zipcode).count(),
        "tool_count": Tool.objects.filter(owner__profile__zone__zipcode=request.user.profile.zone.zipcode).count(),
        "transaction_count": Tool.objects.filter(owner__profile__zone__zipcode=request.user.profile.zone.zipcode).annotate(transactions_count=Count("transactions")).aggregate(Sum("transactions_count"))["transactions_count__sum"]
    }
    return render(request, "ToolShare/pages/stats.html", context)


def layout(request):
    """ renders basic layout (for testing) """
    if "nosidebar" in request.GET:
        baseFile = "ToolShare/base/base_nosidebar.html"
    else:
        baseFile = "ToolShare/base/base_sidebar.html"
    context = {
        "baseFile": baseFile,
        "nobadge": "nobadge" in request.GET
    }
    return render(request, "ToolShare/pages/layout.html", context)


def datepicker(request):
    """ renders basic datepicker (for testing) """
    return render(request, "ToolShare/pages/datepicker.html")


def formtest(request):
    """ renders basic form (for testing) """
    context = {
        "name": request.POST["name"] if "name" in request.POST else ""
    }
    return render(request, "ToolShare/pages/formtest.html", context)

def positiveRating(request, tId, uId):
    """ for a given ToolTransaction (tId), gives a positive rating """
    trans = ToolTransaction.objects.filter(id=tId)[0]
    trans.rating = 1
    trans.save()
    return redirect("ToolShare:UserProfile", uid=uId)

def negativeRating(request, tId, uId):
    """ for a given ToolTransaction (tId), gives a negative rating """
    trans = ToolTransaction.objects.filter(id=tId)[0]
    trans.rating = -1
    trans.save()
    return redirect("ToolShare:UserProfile", uid=uId)
