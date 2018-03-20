from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static

urlpatterns = patterns('ToolShare.viewfiles',

    # misc
    url(r'^$', 'misc.landingPoint', name='LandingPoint'),
    url(r'^statistics/$', 'misc.statistics', name='CommunityStatistics'),
    url(r'^tranactions/postitiverating/(?P<tId>\w+)/(?P<uId>\w+)/$', 'misc.positiveRating', name='PositiveRating'),
    url(r'^tranactions/negativerating/(?P<tId>\w+)/(?P<uId>\w+)/$', 'misc.negativeRating', name='NegativeRating'),

    # login
    url(r'^login/$', 'login.login', name='LogIn'),
    url(r'^logout/$', 'login.logout', name="Logout"),
    url(r'^register/$', 'login.register', name='UserRegistration'),

    # user
    url(r'^dash/$', 'user.dashboard', name='Dashboard'),
    url(r'^user/profile/edit', 'user.editUserProfile', name='EditUserProfile'),
    url(r'^user/profile/(?P<uid>\w+)', 'user.userProfile', name='UserProfile'),
    url(r'^user/profile', 'user.userProfile', name='UserProfile'),
    url(r'^notification/delete/(?P<nid>\w+)', 'user.deleteNotification', name='DeleteNotification'),
    url(r'^notification/$', 'user.notificationList', name='NotificationList'),
    url(r'^mysheds/$', 'user.relevantShed', name='MySheds'),
    # url(r'^user/preferences/$', views.userPreferences, name='UserPreferences'),

    # tool
    url(r'^tool/register/$', 'tool.toolRegistration', name='ToolRegister'),
    url(r'^tool/(?P<toolId>\w+)/$', 'tool.toolDetail', name='IndividualToolDetail'),
    url(r'^tool/(?P<toolId>\w+)/toshed/(?P<shedId>\w+)/$', 'tool.moveToolToShed', name='MoveToolToShed'),
    url(r'^tool/(?P<toolId>\w+)/toowner/(?P<shedId>\w+)/$', 'tool.moveToolToOwner', name='MoveToolToOwner'),
    url(r'^tool/(?P<toolId>\w+)/delete/$', 'tool.deleteTool', name='RemoveTool'),
    url(r'^tool/(?P<toolId>\w+)/borrow/$', 'tool.toolBorrowRequest', name='ToolBorrowRequest'),
    url(r'^tool/lend/(?P<rid>\w+)/$', 'tool.toolApproveLend', name='ApproveLend'),
    url(r'^tool/(?P<toolId>\w+)/return/$', 'tool.toolReturn', name='ReturnTool'),
    url(r'^search/$', 'tool.toolSearchResults', name='ToolSearchResults'),
    # url(r'^tool/(?P<toolId>\w+)/edit/$', views.toolPreferences, name='ToolPreferences'),

    # shed
    url(r'^tool/pick_shed/(?P<toolId>\w+)/$', 'shed.relevantShedSelection', name='ShedSelection'),
    url(r'^shed/register/$', 'shed.shedRegistration', name='CommunityShedRegistration'),
    url(r'^shed/profile/(?P<shedId>\w+)/$', 'shed.shedProfile', name='CommunityShedToolListandProfile'),
    url(r'^shed/private/(?P<shedId>\w+)/requesttojoin/$', 'shed.requestToJoin', name='RequestToJoin'),
    url(r'^shed/private/(?P<shedId>\w+)/addtoshed/(?P<uId>\w+)/$', 'shed.addUserToShed', name='AddUserToShed'),
    url(r'^shed/preferences/(?P<shedId>\w+)/$', 'shed.shedPreferences', name='CommunityShedPreferences'),

    # admin
    #url(r'^/sysadmin/$', views.admin, name='System Administration'),

    # hard coded placeholder
    url(r'^layout', 'misc.layout', name="SampleLayout"),
    url(r'^datepicker', 'misc.datepicker'),
    url(r'^formtest', 'misc.formtest')
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)