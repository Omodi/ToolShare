"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

'''
class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
    def test_basic_addition_WILLFAIL(self):
        """
            Tests that 1 + 1 always equals 2.
            """
        self.assertEqual(1 + 1, 3)
'''

        
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.template.defaultfilters import slugify

from ToolShare.models import Tool, Tag, Shed, ShareZone, Profile, Reservation
from ToolShare import viewfiles as views

import datetime


"""
A note about tests:

Running all tests (including built-in django tests) may result in a couple fails.
You must check if these fails are in the module's code
Certain django contrib tests fail on windows because django can't store session 
data to files on Windows; this is a known issue.

"""
        
        
class ToolRelatedTests(TestCase):
    fixtures = ['initial_data.json']


    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)


    def test_add_tool(self):
        """ 
        Tests that a tool can be added to a user
        """
        
        tools = [
            {
                "name": "Alan Wrench",
                "description": "I got it free from Ikea.",
                "tags": "3-8in hex"
            },
            {
                "name": "Craftsman screwdriver",
                "description": "This description is a duplicate.",
                "tags": "screwdriver craftsman"
            }
        ]

        for tool in tools:
            request = self.factory.post(reverse("ToolShare:ToolRegister"), tool)
            request.user = self.user
            views.tool.toolRegistration(request)
            newTool = Tool.objects.get(name=tool["name"])
            self.assertEqual(newTool.name, tool["name"])
            self.assertEqual(newTool.description, tool["description"])
            for slug in tool["tags"].split(" "):
                slug = slugify(slug)
                self.assertIn(Tag.objects.get(slug=slug), newTool.tags.all())

        # how do we deal with duplicates?


        """
        tool = user.profile.addTool("Alan Wrench", desc="I got it free from Ikea.", tags="3-8in hex")
        self.assertIsInstance(tool, Tool)
        self.assertEqual(tool.name, "Alan Wrench")
        self.assertEqual(tool.description, "I got it free from Ikea.")
        self.assertIn(Tag.objects.get(slug="hex"), tool.tags.all())
        """


    def _add_tool(self):
        """ Helper function, adds tool to active user """
        request = self.factory.post(reverse("ToolShare:ToolRegister"), {
            "name": "test tool",
            "description": "some test tool",
            "tags": "testing"
        })
        request.user = self.user
        views.tool.toolRegistration(request)
        return Tool.objects.get(name="test tool")


    def _add_shed(self):
        """ Helper function, adds shed for active user """
        request = self.factory.post(reverse("ToolShare:CommunityShedRegistration"), {
            "name": "test shed",
            "address": "some address someplace",
            "privateSettings": "0"
        })
        request.user = self.user
        views.shed.shedRegistration(request)
        return Shed.objects.get(name="test shed")


    def test_delete_tool(self):
        """ Adds a tool, then deletes it. Passes if user ends up with 0 tools """
        tool = self._add_tool()
        request = self.factory.get(reverse("ToolShare:RemoveTool", kwargs={
            "toolId": tool.pk
        }))
        request.user = self.user
        request.session = {}
        views.tool.deleteTool(request, toolId=tool.pk)
        self.assertEqual(Tool.objects.filter(pk=tool.pk).count(), 0)


    def test_move_tool_to_shed(self):
        """ User moves tool to shed, checks if tool's location is the shed """
        tool = self._add_tool()
        shed = self._add_shed()
        request = self.factory.get(reverse("ToolShare:MoveToolToShed", kwargs={
            "toolId": tool.pk,
            "shedId": shed.pk
        }))
        request.user = self.user
        request.session = {}
        views.tool.moveToolToShed(request, toolId=tool.pk, shedId=shed.pk)
        self.assertEqual(tool.currentShareLocation(), shed)


    def test_move_tool_to_owner(self):
        """ Piggy backs off of test_move_tool_to_shed, returns tool to owner. Checks tool location. """
        self.test_move_tool_to_shed()
        tool = Tool.objects.get(name="test tool")
        shed = Shed.objects.get(name="test shed")
        request = self.factory.get(reverse("ToolShare:MoveToolToOwner", kwargs={
            "toolId": tool.pk,
            "shedId": shed.pk
        }))
        request.user = self.user
        request.session = {}
        views.tool.moveToolToOwner(request, toolId=tool.pk, shedId=shed.pk)
        self.assertEqual(tool.currentShareLocation(), self.user)


    def test_tool_borrow_request(self):
        """ User2 requests a borrow of User1's tool """
        tool = self._add_tool()
        start = datetime.date.today()
        starts = str(start.month) + "/" + str(start.day) + "/" + str(start.year)
        end = datetime.date.today() + datetime.timedelta(1)
        ends = str(end.month) + "/" + str(end.day) + "/" + str(end.year)
        request = self.factory.post(reverse("ToolShare:ToolBorrowRequest", kwargs={
            "toolId": tool.pk
        }), {
            "startDate": starts,
            "endDate": ends
        })
        request.user = self.user2
        request.session = {}
        views.tool.toolBorrowRequest(request, toolId=tool.pk)
        starts = str(start.year) + "-" + str(start.month) + "-" + str(start.day)
        ends = str(end.year) + "-" + str(end.month) + "-" + str(end.day)
        r = Reservation.objects.filter(start_date__exact=starts, end_date__exact=ends)
        self.assertEqual(r.count(), 1)
        self.assertFalse(r[0].finalized)
        self.assertFalse(r[0].applied)
        return r[0]


    def test_approve_lend(self):
        """ User1 requests the borrow request of User2 (piggy backs off of test_tool_borrow) """
        r = self.test_tool_borrow_request()
        request = self.factory.get(reverse("ToolShare:ApproveLend", kwargs={
            "rid": r.pk
        }))
        request.user = self.user
        request.session = {}
        views.tool.toolApproveLend(request, rid=r.pk)
        r = Reservation.objects.get(pk=r.pk)
        self.assertTrue(r.finalized)
        request2 = self.factory.get(reverse("ToolShare:Dashboard"))
        request2.user = self.user
        request2.session = {}
        views.user.dashboard(request2)
        r = Reservation.objects.get(pk=r.pk)
        self.assertTrue(r.applied)
        self.assertEqual(self.user.notifications.all().count(), 1)
        self.assertEqual(r.tool.transactions.all().count(), 2)
        return r.tool


    def test_return(self):
        """ User2 returns tool to User1 (piggy backs off of test_approve_lend) """
        tool = self.test_approve_lend()
        request = self.factory.get(reverse("ToolShare:ReturnTool", kwargs={
            "toolId": tool.id
        }))
        request.user = self.user2
        request.session = {}
        views.tool.toolReturn(request, toolId=tool.pk)
        tool = Tool.objects.get(pk=tool.pk)
        self.assertEqual(tool.transactions.all().count(), 3)

        
        
class ShedRelatedTests(TestCase):
    fixtures = ['initial_data.json']
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)
    
    def _add_shed(self, privacy, newname, address):
        request = self.factory.post(reverse("ToolShare:CommunityShedRegistration"), {
            "name": newname,
            "address": address,
            "privateSettings": privacy
        })
        request.user = self.user
        views.shed.shedRegistration(request)
        return Shed.objects.get(name=newname)

    def test_add_shed(self):
        """ Tests that a shed can be added by a user """
        new_shed = self._add_shed(0, "public shed", "123 whatever road")
        self.assertEqual(new_shed.name, "public shed")
        self.assertEqual(new_shed.coordinator, self.user)
        self.assertEqual(new_shed.zone, self.user.profile.zone)
        self.assertEqual(new_shed.address, "123 whatever road")
        self.assertEqual(new_shed.searchable, True)
        self.assertEqual(new_shed.invite_only, False)
    
        new_shed2 = self._add_shed(1, "pubprivate shed", "999 whatever street")
        self.assertEqual(new_shed2.name, "pubprivate shed")
        self.assertEqual(new_shed2.coordinator, self.user)
        self.assertEqual(new_shed2.zone, self.user.profile.zone)
        self.assertEqual(new_shed2.address, "999 whatever street")
        self.assertEqual(new_shed2.searchable, True)
        self.assertEqual(new_shed2.invite_only, True)
    
        new_shed3 = self._add_shed(2, "privprivate shed", "2 whatever lane")
        self.assertEqual(new_shed3.name, "privprivate shed")
        self.assertEqual(new_shed3.coordinator, self.user)
        self.assertEqual(new_shed3.zone, self.user.profile.zone)
        self.assertEqual(new_shed3.address, "2 whatever lane")
        self.assertEqual(new_shed3.searchable, False)
        self.assertEqual(new_shed3.invite_only, True)


    def test_shed_update_preferences(self):
        """ User makes a shed, and then changes its name and address. If the changes succeed, this test passes."""
        new_shed = self._add_shed(0, "public shed", "123 whatever road")
        request = self.factory.post(reverse("ToolShare:CommunityShedPreferences", kwargs={
            "shedId":new_shed.pk
        }), {
            "name":"mega shed",
            "address":"my house",
        })
        request.user = self.user
        views.shed.shedPreferences(request, shedId = new_shed.pk)
        altered_shed = Shed.objects.get(name="mega shed")
        self.assertEqual(altered_shed.name, "mega shed")
        self.assertEqual(altered_shed.coordinator, self.user)
        self.assertEqual(altered_shed.zone, self.user.profile.zone)
        self.assertEqual(altered_shed.address, "my house")
        self.assertEqual(altered_shed.searchable, True)
        self.assertEqual(altered_shed.invite_only, False)
        

    def test_relevant_shed_list(self):
        """ Gets all relevant sheds, adds a new one, and checks if it's including in an updated list of relevant sheds. """
        sheds_in_zone = self.user.profile.zone.getAllSheds()
        num_sheds = sheds_in_zone.count()
        self._add_shed(0, "new shed", "120 woop woop lane")
        sheds_in_zone = self.user.profile.zone.getAllSheds()
        self.assertEqual(sheds_in_zone.count(), num_sheds + 1)

    def test_join_shed(self):
        """ User2 requests to join User1's new private shed. This creates a new notification, and if it's created, this succeeds """
        new_shed = self._add_shed(1, "private shed", "mon demain")
        num_notifications = self.user.notifications.count()
        request = self.factory.post(reverse("ToolShare:RequestToJoin", kwargs={
             "shedId":new_shed.pk
        }))
        request.user = self.user2
        request.session = {}
        views.shed.requestToJoin(request, shedId = new_shed.pk)
        self.assertEqual(self.user.notifications.count(), num_notifications + 1)
        return new_shed

    def test_add_user_to_shed(self):
        """ 
        user1 owns a private shed (new_shed)
        user1 accepts user2's request to join, and if the shed gets another member, this succeeds.
        piggy backs off of test_join_shed
        """
        new_shed=self.test_join_shed()
        new_shed=Shed.objects.get(pk=new_shed.pk)
        num_members = new_shed.user_list.count()
        request = self.factory.post(reverse("ToolShare:AddUserToShed", kwargs={
            "shedId":new_shed.pk,
            "uId":self.user2.pk
        }))
        request.user = self.user
        request.session = {}
        views.shed.addUserToShed(request, shedId = new_shed.pk, uId = self.user2.pk)
        self.assertEqual(new_shed.user_list.count(), num_members + 1)
        
        
        
        

class ProfileRelatedTests(TestCase):
    fixtures = ['initial_data.json']
    

    def test_profile_data(self):
        """
        Tests that a user profile contains the data it is set to
        """
        name = "John Smith"
        email = "JohnSmith@rit.edu"
        password = "pswrd"
        zipcode = "12345"
        zone = ShareZone(zipcode=zipcode)
        zone.save()
        user = User.objects.create_user(email, password=password)
        user.save()
        john_profile = Profile(zone=zone, name=name, user=user)
        john_profile.save()
        john_profile = Profile.objects.get(pk=john_profile.pk)
        self.assertEqual(john_profile.name, "John Smith")
        self.assertEqual(john_profile.zone.zipcode, 12345)
        

class NotificationRelatedTests(TestCase):
    fixtures = ['initial_data.json']
    

    def setUp(self):
        self.user_email = "tester@bot.com"
        self.user_name  = "Jimmy Jones"
        zone = ShareZone(zipcode=98765)
        zone.save()
        user = User.objects.create_user(self.user_email, password="pass")
        profile = Profile(zone=zone, name=self.user_name, user=user)
        profile.save()
        if user:
            user.backend = "django.contrib.auth.backends.ModelBackend"
        user.save()
    

    def test_add_notification(self):
        """
        Tests that a user can be sent a notification
        """
        user = User.objects.filter(username=self.user_email)[0]
        self.assertEqual(user.profile.name, self.user_name)
        note_message = "This is a test notification!"
        user.profile.notify(note_message, "#", approve_text="Okay", deny_text="Okay")
        
        notes = user.notifications.count()
        self.assertTrue(notes==1)
        self.assertEqual(user.notifications.filter(message=note_message).count(), 1)
        
        
class ShareZoneRelatedTests(TestCase):
    fixtures = ['initial_data.json']
    

    def test_add_sharezone(self):
        """
        Tests that a share zone can be added
        """
        zone = ShareZone(zipcode=19067)
        zone.save()
        zone = ShareZone.objects.get(zipcode=19067)
        self.assertEqual(zone.zipcode,19067)