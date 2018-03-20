def notifications(request):
    """ makes sure the user is logged in before notifications are retrieved """
    if request.user.is_authenticated():
        return {"notifications": request.user.notifications.all()}
    else:
        return {}