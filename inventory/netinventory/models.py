from django.db import models

# Node details using for connection to device:
class Nodes(models.Model):
    ip = models.GenericIPAddressField()
    username = models.TextField()
    passwd = models.CharField(max_length=255)
    snmpcommunity = models.TextField()
 #  vendor = models.TextField()   # to detect cisco ios/ios-xe/ios-xr
    class Meta:
        verbose_name='Nodes'
        verbose_name_plural='Nodes'
        ordering=['ip']
 #TODO check it:
 #       permissions = [('can_add_node', 'Can add node'),
 #                      ('can_delete_node', 'Can delete node')]

# ssh_private_key   # TODO test ssh_private_key
# ??? port -

# For inventory output:
class Inventory(models.Model):
    hostname = models.TextField()
    ip=models.GenericIPAddressField()
    description = models.TextField()  # module name/description #TODO change the name in DB
    vendor = models.TextField()
    part_number = models.TextField()
    serial_number = models.TextField(unique=True)
    site = models.TextField()  #TODO change its name to location
    timestamp = models.DateTimeField(auto_now=True) # TODO change to creation

# For scan logging
class ScanLog(models.Model):
    ip = models.GenericIPAddressField()
    log = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)

# For node inventory logging ---> track items moving
class InventoryLog(models.Model):
    ip = models.GenericIPAddressField()
    hostname = models.TextField()
    name = models.TextField()
    serial_number = models.TextField()
    site = models.TextField()
    log_description = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)