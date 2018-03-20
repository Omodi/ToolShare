from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import query, Count, Sum
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse


class ToolTransaction(models.Model):
    """ Manages the history of a tool; also used to store where a tool currently is """
    
    object_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    current_holder = generic.GenericForeignKey('object_type','object_id')
    time = models.DateTimeField(auto_now_add=True)
    tool = models.ForeignKey('Tool', null=False, blank=False, related_name='transactions')
    rating = models.IntegerField(default=0)
    """ The rating is of the current_holder of the tool, by the last current_holder """
    
    def holderIsShed(self):
        """ Finds if the current_holder is a Shed """
        
        return isinstance(self.current_holder, Shed)
    
    def __getattribute__(self, obj):
        """ Delicious metahackery to let us call 'functions' in templates """
        
        if obj == "holder":
            """ Redirect to current transaction holder name """
            return self.current_holder
        else:
            return super(ToolTransaction, self).__getattribute__(obj)

    def getPrev(self):
        """ returns the previous ToolTransaction for this Tool, if there is one. """
        
        try:
            return self.tool.transactions.filter(time__lt=self.time).order_by('-time')[0]
        except IndexError:
            return None
                    
    def __str__(self):
        return str(self.current_holder) + "@" + str(self.time)

    class Meta():
        get_latest_by = "time"
        
class Reservation(models.Model):
    """ Manages the future availability of a tool """
    
    start_date = models.DateField()
    end_date = models.DateField()
    creation_date_time = models.DateTimeField(auto_now_add=True)
    tool = models.ForeignKey('Tool', null=False, blank=False, related_name='reservations')
    finalized = models.BooleanField(default=False)
    applied = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True, blank=True, related_name='reservations')
    
    def __str__(self):
        return str(self.user) + " wants " + str(self.tool) + " from " + str(self.start_date) + " to " + str(self.end_date)

        
class Tag(models.Model):
    """ 'Singleton' tags to search by """
    
    slug = models.SlugField(unique=True)

    def __str__(self):
        return str(self.slug)

        
class Tool(models.Model):
    """ Grand repository of information on a tool """
    
    name = models.CharField("Tool Name", max_length=20)
    description = models.TextField("Tool Description", blank=True)
    tags = models.ManyToManyField(Tag, related_name='tools')
    owner = models.ForeignKey(User, related_name='tools')
    
    

    def __getattribute__(self, obj):
        """ Delicious metahackery to let us call 'functions' in templates """
        
        if obj == "shareLocation":
            """ Redirect to current share location's name """
            
            cur_loc = self.currentShareLocation()
            if isinstance(cur_loc, Shed):
                return cur_loc.name
            else:
                return cur_loc.profile.name
        elif obj == "sharelocation":
            """ Redirect to current share location's object """
            
            cur_loc = self.currentShareLocation()
            if isinstance(cur_loc, Shed):
                return cur_loc
            else:
                return cur_loc.profile
        elif obj == "in_shed":
            """ Renturns if the tool is in a Shed """
            
            cur_loc = self.currentShareLocation()
            return isinstance(cur_loc, Shed)
        elif obj == "current_holder":
            """ Redirect to current holder's name """
            
            cur_loc = self.currentHolder()
            if isinstance(cur_loc, Shed):
                return cur_loc.name
            else:
                return cur_loc.profile.name
        elif obj == "holder":
            """ Redirect to current holder's object """
            
            cur_loc = self.currentHolder()
            return cur_loc
        elif obj == "zone":
            """ Redirect to zone """
            return self.owner.profile.zone
        elif obj == "popular_tags": # 7 most popular tags on this item
            return self.tags.annotate(tool_count=Count('tools')).distinct().order_by('-tool_count')[0:7]
        else:
            return super(Tool, self).__getattribute__(obj)

    def currentHolder(self):
        """ Returns where the tool currently is """
        
        return self.transactions.latest().current_holder

    def currentShareLocation(self):
        """ Returns the current user or shed from which this tool is being lent """
        
        transacts = self.transactions.order_by("time")
        place = transacts.latest()
        if (place.current_holder == self.owner or isinstance(place.current_holder, Shed)):
            return place.current_holder
        elif (transacts.count() < 2):
            """tool has not had a full transaction yet"""
            return place.current_holder
        return transacts[transacts.count()-2].current_holder

    def isAvailable(self):
        """ Returns whether the tool is available to be borrowed """
        
        return (self.currentShareLocation() == self.currentHolder())

    def movedTo(self, shed_or_user):
        """ Move the tool into the possession of a new holder; shed or user """
        
        trans = ToolTransaction(current_holder=shed_or_user, tool=self)
        trans.save()
        self.save()
            
    def __str__(self):
        return str(self.name)


class Profile(models.Model):
    """ Contains the information and functionality of the user that is not auth-related """
    
    name = models.CharField("Name", max_length=30, blank=True)
    zone = models.ForeignKey('ShareZone')
    address = models.TextField("Address", blank=True)
    user = models.OneToOneField(User, related_name='profile')
    method = models.TextField("Method Of Sharing", blank=True)

    def borrowedTools(self):
        """ Returns a list of all tools the user is currently borrowing """
        
        ret = []
        for tool in self.zone.getAllTools():
            if (tool.currentHolder() == self.user) and (tool.owner != self.user):
                ret += [tool]
        return ret
    
    def addTool(self, name, desc=None, tags=None):
        """ Add a new tool into a user's cache of tools """
        
        tool = Tool(name=name, description=desc, owner=self.user)
        tool.save()
        trans = ToolTransaction(current_holder=self.user, tool=tool)
        trans.save()

        banned_tags_file = open("banned_words.txt", "r")
        banned_tags = []
        for line in banned_tags_file:
            line = line.lower().strip()
            if line and line[0]=="#":
                continue
            banned_tags += [slugify(line)]

        allTags = Tag.objects.all()
        tagList = set((tags+" "+name).lower().strip().split(" "))
        for t in tagList:
            if slugify(t) in banned_tags: 
                continue
            same = False
            for temp in allTags:
                if slugify(t) == temp.slug:
                    same = True
                    tool.tags.add(temp)
                    tool.save()
                    break
            if not same:
                tag = Tag(slug=slugify(t))
                tag.save()
                tool.tags.add(tag)

        trans.save()
        tool.save()
        self.save()

        return tool
    
    def __str__(self):
        return name

    def notify(self, message, shortcut=None, approve_text="Accept", deny_text="Deny"):
        """ Send a notification to a user with the given content """
        
        if shortcut:
            note = Notification(message=message, shortcut=shortcut, user=self.user, \
                approve_text=approve_text, deny_text=deny_text)
            note.save()
        else:
            note = Notification(message=message, shortcut=reverse("ToolShare:Dashboard"), user=self.user, \
                approve_text=None, deny_text="Dismiss")
            note.save()
    
    def getRating(self):
        """ returns Sum of all ToolTransactions involving User """
        return ToolTransaction.objects.filter(object_id=self.id).aggregate(Sum("rating"))["rating__sum"]

    def __str__(self):
        return str(self.user) + " (" + str(self.zone) + ")"
            
        
class Shed(models.Model):
    """ Contains information required to share tools in a community shed """
    
    name = models.CharField("Community Shed Name", max_length=30, blank=True)
    zone = models.ForeignKey('ShareZone')
    address = models.TextField("Address", blank=True)
    coordinator = models.ForeignKey(User, related_name='my_sheds')
    # Private-shed fields
    user_list = models.ManyToManyField(User)
    searchable = models.BooleanField(default=True)
    invite_only = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)


class Notification(models.Model):
    """
    Contains all of the information necessary for a user to read and respond to notifications
    
    Note: Approving a notification triggers a redirect to the shortcut, deny will not.
    In either case, any reply will remove the notification.
    """
    
    time = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    shortcut = models.URLField()
    approve_text = models.CharField(max_length=15, default="Accept", null=True, blank=True)
    deny_text = models.CharField(max_length=15, default="Deny")
    user = models.ForeignKey(User, related_name='notifications')

    def __str__(self):
        return str(self.message) + "@" + str(self.time) + " for " + str(self.user.profile.name)


class ShareZone(models.Model):
    """ A container to store locally-related things (sheds, users, the tools therein) by zipcode """
    
    zipcode = models.PositiveIntegerField(verbose_name="Zipcode", primary_key=True, unique=True)

    def getAllTools(self):
        """Returns -all- tools in zipcode."""
        
        return Tool.objects.filter(owner__profile__zone__zipcode__exact=self.zipcode)

    def getAllAvailableTools(self):
        """Needs revision; used to filter by canBorrow, canBorrow does not exist anymore"""
        
        return self.getAllTools()

    def getAllSheds(self):
        """ Returns all community sheds within the zone """
        
        return Shed.objects.filter(zone=self)
    
    def __str__(self):
        return "{:0>5}".format(self.zipcode)