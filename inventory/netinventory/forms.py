from django import forms
from .models import Nodes, Inventory, InventoryLog

# TODO remove this form and replase with a single Nodes form
class Setnode(forms.Form):
    ip = forms.CharField(max_length=255, label='Node IP:')
    username = forms.CharField(max_length=30, label='Username:')
    passwd = forms.CharField(max_length=255, label='Password:')
    snmpcommunity = forms.CharField(max_length=30, label='SNMP community:')
    class Node:
        model = Nodes
        fields = [
            'ip',
            'username',
            'passwd',
            'snmpcommunity'
        ]
# TODO remove this form and replase with a single Nodes form
class Editnode(forms.Form):
    ip = forms.CharField(max_length=255, required=False,label='Node IP:')
    username = forms.CharField(max_length=30, required=False,label='Username:')
    passwd = forms.CharField(max_length=255, required=False,label='Password:')
    snmpcommunity = forms.CharField(max_length=30,required=False, label='SNMP community:')
    class Node:
        model = Nodes
        fields = [
            'ip',
            'username',
            'passwd',
            'snmpcommunity'
        ]

class Invout(forms.Form):
    # TODO what if nothing in tables (first start)? Test

    host_choices = [('all', 'Select all')] + [(i['hostname'], i['hostname']) for i in
                                            Inventory.objects.values('hostname').distinct()]
    ip_choices = [('all', 'Select all')] + [(i['ip'], i['ip']) for i in
                                            Nodes.objects.values('ip').distinct()]
    site_choices = [('all', 'Select all')] + [(i['site'], i['site']) for i in
                                              Inventory.objects.values('site').distinct()]
    module_choices = [('all', 'Select all')] + [(i['description'], i['description']) for i in
                                              Inventory.objects.values('description').distinct()]
    vendor_choices = [('all', 'Select all')] + [(i['vendor'], i['vendor']) for i in
                                                Inventory.objects.values('vendor').distinct()]
    hostname=forms.ChoiceField(choices=host_choices, label='Hostname:')
    ip=forms.ChoiceField(choices=ip_choices, label='IP:')
    site=forms.ChoiceField(choices=site_choices, label='Site:')
    description=forms.ChoiceField(choices=module_choices, label='HW model:')
    serial_number=forms.CharField(max_length=40, required=False,label='Serial number:')
    vendor=forms.ChoiceField(choices=vendor_choices, label='Vendor:')

    class Meta:
        model = Inventory
        fields = [
            'hostname',
            'ip',
            'site',
            'description',
            'serial_number'
            'vendor',
        ]

class Inventorylog(forms.Form):
    host_choices = [('all', 'Select all')] + [(i['hostname'], i['hostname']) for i in
                                              InventoryLog.objects.values('hostname').exclude(hostname='').distinct()]
    site_choices = [('all', 'Select all')] + [(i['site'], i['site']) for i in
                                              InventoryLog.objects.values('site').exclude(site='').distinct() if i is not None]
    hwname_choice = [('all', 'Select all')] + [(i['name'], i['name']) for i in
                                              InventoryLog.objects.values('name').exclude(name='').distinct() if i is not None]
    ip = forms.CharField(max_length=255, required=False, label='Node IP:')
    name = forms.ChoiceField(choices=hwname_choice, label='HW name', required=False,)
    hostname=forms.ChoiceField(choices=host_choices, label='Hostname:')
    serial_number=forms.CharField(max_length=40, required=False, label='Serial number:')
    site=forms.ChoiceField(choices=site_choices, label='Site:')
    class Node:
        model = Nodes
        fields = [
            'ip',
            'hostname',
            'name',
            'serial_number',
            'site',
        ]
