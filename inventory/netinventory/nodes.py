
from .models import *
from .forms import *
from snmp import Manager
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
from ncclient import manager as node
from ncclient.transport.errors import SSHError
from django.core.cache import cache
from lxml import etree
import jxmlease
from jnpr.junos import Device
import re

def valid_ip(address):
    try:
        host_bytes = address.split('.')
        valid = [int(b) for b in host_bytes]
        valid = [b for b in valid if b >= 0 and b<=255]
        return len(host_bytes) == 4 and len(valid) == 4
    except:
        return False

def inv_log(ip, action):
    # TODO what if 'site' wasn't got during the scan ??? TEST IT
    user=cache.get('_cached_user')
    if Inventory.objects.filter(ip=ip).exists():
        hostname = Inventory.objects.filter(ip=ip).values('hostname').distinct('hostname')
        site=Inventory.objects.filter(ip=ip).values('site').distinct('site')
    else:
        hostname=''
        site=''

    InventoryLog.objects.create(ip=ip, hostname=hostname, site=site, \
                                log_description='Node was {} (user {})'.format(action, user))



def add(form):
    msg=[]
    if form.is_valid():
        if valid_ip(form.cleaned_data.get('ip')):
            ip = form.cleaned_data.get('ip')
        else:
            msg.append('Error: Invalid input syntax for IP address.')
            return (msg)
        if Nodes.objects.filter(ip=ip).values():
            msg.append('Error: Node already exists')
        else:
            Nodes.objects.create(ip=form.cleaned_data.get('ip'),
                                 username=form.cleaned_data.get('username'),
                                 #             passwd=make_password(form.cleaned_data.get('passwd')),
                                 passwd=form.cleaned_data.get('passwd'),
                                 snmpcommunity=form.cleaned_data.get('snmpcommunity')
                                 )
            invent_log = inv_log(ip, action='created')

            msg.append('Node added')
    return(msg)

def delete(ip):
    try:
        Nodes.objects.filter(ip=ip).delete()
        Inventory.objects.filter(ip=ip).delete()
        msg = ('{} was sucessfully deleted'.format(ip))
        status='done'
        invent_log = inv_log(ip, action='deleted')
    except:
        msg = ('Error during delete')
        status='error'
        pass
    return(status, msg)

def edit(id,form):
    msg = []
    newip = ''
    newusername = ''
    newpasswd = ''
    newsnmpcommunity = ''
    thostname = ''
    ip=Nodes.objects.values_list('ip', flat=True).get(id=id)
    hostname=Inventory.objects.filter(ip=ip).values('hostname').distinct('hostname')
    if form.is_valid():
        if form.has_changed():
            if form.cleaned_data.get('ip'):
                if valid_ip(form.cleaned_data.get('ip')):
                    newip = form.cleaned_data.get('ip')
                else:
                    msg.append('Error: Invalid input syntax for IP address.')
                    return (msg)
            else:
                 newip = ip

            if form.cleaned_data.get('username'):
                 newusername = form.cleaned_data.get('username')
            else:
                 for i in Nodes.objects.filter(id=id).values('username'):
                     newusername = i['username']

            if form.cleaned_data.get('passwd'):
                 newpasswd = form.cleaned_data.get('passwd')
            else:
                for i in Nodes.objects.filter(id=id).values('passwd'):
                    newpasswd = i['passwd']
            if form.cleaned_data.get('snmpcommunity'):
                newsnmpcommunity = form.cleaned_data.get('snmpcommunity')
            else:
                for i in Nodes.objects.filter(id=id).values('snmpcommunity'):
                    newsnmpcommunity = i['snmpcommunity']
            if ip != newip and Nodes.objects.filter(ip=newip).exists():
                for i in Inventory.objects.filter(ip=newip).values('hostname').distinct('hostname'):
                    thostname = i['hostname']
                    msg.append("The Selected IP {} already assigned to {}".format(newip, thostname))
            else:
                Nodes.objects.update_or_create(ip=ip, \
                                               defaults={
                                                   'ip': newip,
                                                   'username': newusername,
                                                   'passwd': newpasswd,
                                                   'snmpcommunity': newsnmpcommunity,
                                                   })
                msg.append('Node settings were successfully updated.')
                if Inventory.objects.filter(ip=ip).exists():
                    Inventory.objects.filter(ip=ip).update(ip=newip)
                    msg.append('Inventory was successfully updated.')
                invent_log=inv_log(ip, action='edited')
        else:
            msg.append('Nothing is selected.')
    return(msg)

# test snmp and netconf connections
def test(id):
    out=''
    result=[]
    ip= Nodes.objects.values_list('ip', flat=True).get(id=id)
    username= Nodes.objects.values_list('username', flat=True).get(id=id)
    passwd= Nodes.objects.values_list('passwd', flat=True).get(id=id)
    snmpcommunity= Nodes.objects.values_list('snmpcommunity', flat=True).get(id=id)
    snmpcommunity=str(snmpcommunity).encode('ascii')

#########################################################
# Test SNMP
# 1.3.6.1.2.1.1.1.0      - sysDescr (all platforms).
    # for Juniper - do not use 'set snmp description ...' as it is overwrite built-in sysDescr
    #
#########################################################

    manager = Manager(snmpcommunity)
    oids = ["1.3.6.1.2.1.1.1.0"]
    try:
        vars=manager.get(ip, *oids)
        for var in vars:
    ## 	OCTET_STRING: b'Cisco IOS XR Software (IOS-XRv 9000), Version 6.3.3\r\nCopyright (c) 2013-2017 by Cisco Systems, Inc.'
    ##  OCTET_STRING: b'Cisco IOS Software, IOS-XE Software, Catalyst L3 Switch Software (CAT3K_CAA-UNIVERSALK9-M), Version 03.06.04.E RELEASE SOFTWARE (fc2)\r\nTechnical Support: http://www.cisco.com/techsupport\r\nCopyright (c) 1986-2016 by Cisco Systems, Inc.\r\nCompiled Sat 13-Feb'

  #          t=str(var).split(' ', 2)[2].split(' ')[0][2:]
            vendor=str(var).split(' ', 2)[2].split(' ')[0][1:].replace("'","")
            if vendor == 'Cisco':
       #         version = str(var).split(' ', 2)[2].split(' ')[2]
                version=str(var).split(' ', 2)[2][1:].split(' ')
                if 'XR' in version:
                    vendor = 'Cisco IOS-XR'
                elif 'IOS-XE' in version:
                    vendor = 'Cisco IOS-XE'
        result.append("SNMP - OK")

    except NoSuchName as n: #TODO do I need it ???
        out = ("SNMP test - Failed (NoSuchName})")
        ScanLog.objects.create(ip=ip,
                               log="SNMP test - Failed (Timeout)")
        pass
    except Timeout as e:
        out = ("SNMP test - Failed (Timeout)")
        ScanLog.objects.create(ip=ip,
                               log="SNMP test - Failed (Timeout)")
        result.append(out)
        vendor=''
        pass
    finally:
        manager.close()

#########################################################
# Test credentials for netconf (port=830)
#########################################################

#    via PyEZ:
#    dev = Device(host=ip, port=830, user=username, password=passwd, normalize=True, hostkey_verify=False)
#    try:
#        dev.open()
#        dev.close()
#        out = ("NETCONF - OK")
#        result.append(out)
#    except:
#        out = ("NETCONF test - Failed")
#        result.append(out)

#TODO do netconf test and getinventory using ncclient (if possible)

    if vendor == 'Juniper':
        try:
            conn = node.connect(host=ip, port=830, username=username, password=passwd, timeout=10,
                                device_params={'name':'junos'},
                                hostkey_verify=False)
            conn.close_session()
            result.append("NETCONF - OK")
        except SSHError as e:
            result.append("NETCONF test - Failed")
            ScanLog.objects.create(ip=ip,
                                   log="Error: NETCONF test - Failed {}".format(e))
        except:
            result.append("NETCONF test - Failed")
    elif vendor == 'Cisco IOS-XR':
        try:
            conn = node.connect(host=ip, port=830, username=username, password=passwd, timeout=10,
                               device_params={'name':'iosxr'},
                               hostkey_verify=False,
                               allow_agent=False)
            tconf = conn.get_config(source='running').data_xml  # it works (returns running config) !!!
            inventory_filter = '''
                                   <platform-inventory xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-plat-chas-invmgr-ng-oper"/>
                                           '''
            tresult = conn.get(filter=('subtree', inventory_filter)).data_xml
            conn.close_session()
            result.append("NETCONF - OK")

        except SSHError as e:
            result.append("NETCONF test - Failed")
            ScanLog.objects.create(ip=ip,
                                   log="Error: NETCONF test - Failed {}".format(e))
    elif vendor == 'Cisco IOS-XE':
        try:
            conn = node.connect(host=ip, port=22, username=username, password=passwd, timeout=10,
                                device_params={'name':'iosxe'},
                                hostkey_verify=False,
                                allow_agent=False)

            tconf = conn.get_config(source='running').data_xml  # it works (returns running config) !!!


         #   inventory_filter = '''
         #                      <platform-inventory xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper"/>
         #                             '''
         #   tresult = conn.get(filter=('subtree', inventory_filter)).data_xml
         #   print(tresult)
            conn.close_session()
            result.append("NETCONF - OK")

        except SSHError as e:
            result.append("NETCONF test - Failed")
            ScanLog.objects.create(ip=ip,
                                   log="Error: NETCONF test - Failed {}".format(e))
    else:
        result.append("NETCONF test - Failed")
    return(result)