from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404
from ToolShare.models import Reservation
import datetime

def check_reservations(func):
    """ If a scheduled reservation has come up, makes the transaction """
    def wrapper_inner(*args, **kwargs):
        # First, get all reservations whose start dates have passed
        to_apply = Reservation.objects.filter(start_date__lt=(datetime.date.today()+datetime.timedelta(days=1)), finalized=True, applied=False)
        for obj in to_apply:
            if obj.user: # Not a blackout date
                obj.tool.movedTo(obj.user) # apply transaction
            obj.applied = True
            obj.save()
        # Get all of the reservations whose start date has passed and remove them
        to_remove = Reservation.objects.filter(end_date__lt=(datetime.date.today()+datetime.timedelta(days=1)))
        for obj in to_remove:
            obj.delete()
        return func(*args, **kwargs)
    return wrapper_inner

def object_required(class_object, key, allow_none=False):
    """ Makes sure the specific (identified by key) object (identified by class_object) exists"""
    def wrapper(func):
        def wrapper_inner(*args, **kwargs):
            if not allow_none and key not in kwargs:
                raise Http404
            if key in kwargs and kwargs[key]:
                get_object_or_404(class_object, pk=kwargs[key])
            elif not allow_none:
                raise Http404
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper

def sharezone_required(class_object, key, allow_none=False):
    """ Makes sure the object (type defined by class_object, identified by key) is in the ShareZone of the User"""
    def wrapper(func):
        def wrapper_inner(request, *args, **kwargs):
            if key in kwargs:
                instance = class_object.objects.get(pk=kwargs[key])
                if class_object == User:
                    instance = instance.profile
                if instance.zone != request.user.profile.zone:
                    raise Http404
            else:
                if not allow_none:
                    raise Http404
            return func(request, *args, **kwargs)
        return wrapper_inner
    return wrapper