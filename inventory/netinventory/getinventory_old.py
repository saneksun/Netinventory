
from .models import *
from snmp import Manager
from snmp.exceptions import Timeout
from django.db import IntegrityError
from ncclient import manager as node
from ncclient.transport.errors import SSHError
from datetime import datetime,timedelta
from jnpr.junos import Device
from lxml import etree
import jxmlease
import re

def sys_hardware(ips):
    error = []
    sresult = []

    for ip in ips:
        username= Nodes.objects.values_list('username', flat=True).get(ip=ip)
        passwd= Nodes.objects.values_list('passwd', flat=True).get(ip=ip)
        snmp_comm = Nodes.objects.values_list('snmpcommunity', flat=True).get(ip=ip)
        snmp_comm = str(snmp_comm).encode('ascii')

#################################################
#    snmp - get vendor by sysDescr
#################################################

        manager = Manager(snmp_comm)
        try:
            oids = ["1.3.6.1.2.1.1.1.0"]
            vars = manager.get(ip, *oids)
            for var in vars:
                #   tvendor = str(var).split(' ', 2)[2].split(' ')[0][2:]
                tvendor=str(var).split(' ', 2)[2].split(' ')[0][1:].replace("'","")

                if tvendor == 'Cisco':
                    version = str(var).split(' ', 2)[2][1:].split(' ')
                    if 'XR' in version:
                        tvendor = 'Cisco IOS-XR'
                    elif 'IOS-XE' in version:
                        tvendor = 'Cisco IOS-XE'
        except Timeout as e:
            tvendor=''
            pass
        finally:
            manager.close()

#################################################
#    Device scan
#################################################

        if tvendor=='Juniper':

#################################################
#    Juniper Network SNMP
#################################################
            # Get site name from OID: '1.3.6.1.2.1.1.6.0' - snmp location
            # TODO - try to get location via netconf
            manager = Manager(snmp_comm)
            try:
                oids = ['1.3.6.1.2.1.1.6.0']
                vars = manager.get(ip, *oids)
                for var in vars:
                 #   site = str(var).split(' ', 2)[2].split(',')[0][2:]
        #            print(re.findall(r'(?<=OCTET_STRING: b).*$', str(var))[0].split(',')[1:])#.replace("'",""))
                    site =str(re.findall(r'^[^,]*,[^,]*\b\w+\b',str(re.findall(r'(?<=OCTET_STRING: b).*$', str(var))[0].replace("'","")))[0])
               # TODO change site to the following:
               #     site=str(re.findall(r'(?<=OCTET_STRING: b).*$', str(var))[0].replace("'",""))
                    sresult.append("SNMP request to host {} - done".format(ip))
            except Timeout as e:
                sresult.append("Request for {} from host {} timed out".format(e, ip))
            finally:
                manager.close()

#################################################
#    Juniper Network NETCONF
#################################################

# ncclient:
#        conn = node.connect(host=ip, port=830, username=username, password=passwd, timeout=10,
#                                device_params={'name':'junos'},
#                                hostkey_verify=False)
#   GET INVENTORY:
#        rpc = conn.get_chassis_inventory().data_xml
#        hw_result=jxmlease.parse(rpc)
#   GET HOSTNAME:
#        rpc = conn.get_software_information().data_xml
#        dd=jxmlease.parse(rpc)
#        print(dd['rpc-reply']['software-information']['host-name'])
#        conn.close_session()
#
#
#  pyez:
#        dev = Device(host=ip, port=830, user=username, password=passwd,
#                     normalize=True,
#                     hostkey_verify=False)
#        dev.open()
#
#        hostname = str(dev.facts['hostname'])
        # get inventory information
#        rpc = dev.rpc.get_chassis_inventory()
#        rpc_xml = etree.tostring(rpc, pretty_print=True, encoding='unicode')
#        dev.close()
################

            conn = node.connect(host=ip, port=830, username=username, password=passwd, timeout=10,
                                device_params={'name':'junos'},
                                hostkey_verify=False)
       #   GET INVENTORY:
            rpc = conn.get_chassis_inventory().data_xml
            hw_result=jxmlease.parse(rpc)
            print(hw_result)
       #   GET HOSTNAME:
            rpc = conn.get_software_information().data_xml
            dd=jxmlease.parse(rpc)
            print(dd['rpc-reply']['software-information']['host-name'])
            conn.close_session()

################
            vendor = 'Juniper Network'
            try:
                dev = Device(host=ip, port=830, user=username, password=passwd,
                             normalize=True,
                             hostkey_verify=False)
                dev.open()

                hostname = str(dev.facts['hostname'])
        # get inventory information
                rpc = dev.rpc.get_chassis_inventory()
                rpc_xml = etree.tostring(rpc, pretty_print=True, encoding='unicode')
                dev.close()
                result = jxmlease.parse(rpc_xml)
    #            chassis_type = str(result['chassis-inventory']['chassis']['description'])

                if any('chassis-sub-module' in modules for modules in result['chassis-inventory']['chassis']['chassis-module']):
                    for modules in result['chassis-inventory']['chassis']['chassis-module']:
                        if re.match(r'Routing Engine \d', str(modules.get('name'))) is None:
                            try:
                                description = str(modules['model-number'])
                                part_number = str(modules['part-number'])
                                serial_number = str(modules['serial-number'])
                                Inventory.objects.create(hostname=hostname, ip=ip, description=description, \
                                                         part_number=part_number, \
                                                         site=site, serial_number=serial_number, vendor=vendor)
                            except IntegrityError as db_err:  # s/n already exists in DB
                                check_ip = Inventory.objects.values_list('ip', flat=True).get(serial_number=serial_number)
                                # if s/n exists in DB for the same node (IP):
                                if check_ip == ip:
                                    scan_time = str(datetime.now())
                                    Inventory.objects.filter(serial_number=serial_number).update(timestamp=scan_time,
                                                                                                 hostname=hostname,
                                                                                                 site=site)
                                # if s/n exists in DB for another node (IP):                                                                hostname=hostname)
                                else:
                                    error.append(str("Error {} for {}".format(str(db_err).split('\n')[1], check_ip)))
                                    ScanLog.objects.create(ip=ip,
                                                           log="Error scanning node {}. {} for {}".format(ip, \
                                                               str(db_err).split('\n')[1], check_ip))

                        if modules.get('chassis-sub-module'):
                            for submodules in modules.get('chassis-sub-module'):
                                if submodules.get('chassis-sub-sub-module'):
                                    for items in submodules.get('chassis-sub-sub-module'):
                                        try:
                                            description = str(items['description'])
                                            part_number = str(items['part-number'])
                                            serial_number = str(items['serial-number'])
                                            Inventory.objects.create(hostname=hostname, ip=ip, description=description, \
                                                                     part_number=part_number, \
                                                                     site=site, serial_number=serial_number, vendor=vendor)
                                        except IntegrityError as db_err:
                                            check_ip = Inventory.objects.values_list('ip', flat=True).get(serial_number=serial_number)
                                            if check_ip == ip:
                                                scan_time = str(datetime.now())
                                                Inventory.objects.filter(serial_number=serial_number).update(timestamp=scan_time,
                                                                                                             hostname=hostname,
                                                                                                             site=site)
                                            else:
                                                error.append(str("Error {} for {}".format(str(db_err).split('\n')[1], check_ip)))
                                                ScanLog.objects.create(ip=ip,
                                                                       log="Error scanning node {}. {} for {}".format( \
                                                                        ip, str(db_err).split('\n')[1], check_ip))

                                            continue
                                elif submodules.get('serial-number') and str(submodules.get('serial-number')) != 'BUILTIN':
                                    try:
                                        description = str(submodules['model-number'])
                                        part_number = str(submodules['part-name'])
                                        serial_number = str(submodules['serial-number'])
                                        Inventory.objects.create(hostname=hostname, ip=ip, description=description, \
                                                                 part_number=part_number, \
                                                                 site=site, serial_number=serial_number, vendor=vendor)
                                    except IntegrityError as db_err:
                                        check_ip=Inventory.objects.values_list('ip', flat=True).get(serial_number=serial_number)
                                        if check_ip == ip:
                                            scan_time = str(datetime.now())
                                            Inventory.objects.filter(serial_number=serial_number).update(timestamp=scan_time,
                                                                                                         hostname=hostname,
                                                                                                         site=site)
                                        else:
                                            error.append(str("Error {} for {}".format(str(db_err).split('\n')[1], check_ip)))
                                            ScanLog.objects.create(ip=ip,
                                                                   log="Error scanning node {}. {} for {}".format( \
                                                                       ip, str(db_err).split('\n')[1], check_ip))
                                        continue
                else:
                    description = str(result['chassis-inventory']['chassis']['description'])
                    part_number = str(result['chassis-inventory']['chassis'].get('description'))
                    serial_number = str(result['chassis-inventory']['chassis'].get('serial-number'))
                    try:
                        Inventory.objects.create(hostname=hostname, ip=ip, description=description, \
                                                 part_number=part_number, \
                                                 site=site, serial_number=serial_number, vendor=vendor)
                    except IntegrityError as db_err:
                        check_ip = Inventory.objects.values_list('ip', flat=True).get(serial_number=serial_number)
                        if check_ip==ip:
                            scan_time = str(datetime.now())
                            Inventory.objects.filter(serial_number=serial_number).update(timestamp=scan_time,
                                                                                         hostname=hostname,
                                                                                         site=site)
                        else:
                            error.append(str("Error {} for {}".format(str(db_err).split('\n')[1], check_ip)))
                            ScanLog.objects.create(ip=ip,
                                                   log="Error scanning node {}. {} for {}".format( \
                                                       ip, str(db_err).split('\n')[1], check_ip))
                        pass
            except:
                error.append("NETCONF test - Failed")
                ScanLog.objects.create(ip=ip,
                                       log="NETCONF test - Failed for {}".format(ip))

#################################################
#    Cisco NETCONF
#################################################

        elif tvendor=='Cisco IOS-XR':
            vendor = 'Cisco Systems'

            try:
                conn = node.connect(host=ip, port=830, username=username, password=passwd, timeout=10,
                                    device_params={'name': 'iosxr'},
                                    hostkey_verify=False,
                                    allow_agent=False)
                # TODO as netinv doesn't require high privilege level running config doesn't acceptable
                tconf = conn.get_config(source='running').data_xml  # it works (returns running config) !!!
                inventory_filter = '''
                       <platform-inventory xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-plat-chas-invmgr-ng-oper"/>
                               '''
                tresult = conn.get(filter=('subtree', inventory_filter)).data_xml
                conn.close_session()

                location=jxmlease.parse(tconf)['data']['snmp']['system']['location']
                site = str(re.findall(r'^[^,]*,[^,]*', location)[0])
                hostname = jxmlease.parse(tconf)['data']['host-names']['host-name']
                temp = jxmlease.parse(tresult)
                for cards in temp['data']['platform-inventory']['racks']['rack']['slots']['slot']:
                    if 'modules' in cards['cards']['card']:
                        for module in cards['cards']['card']['modules']['module']:
                            if type(module) is jxmlease.dictnode.XMLDictNode:
                                if 'attributes' in module['hw-components']['hw-component']:
                                    description = str(module['hw-components']['hw-component']['attributes']['basic-info']['model-name'])
                                    part_number = str(module['hw-components']['hw-component']['attributes']['basic-info']['name'])
                                    serial_number = str(module['hw-components']['hw-component']['attributes']['basic-info']['serial-number'])
                                    try:
                                        Inventory.objects.create(hostname=hostname, ip=ip, description=description, \
                                                                 part_number=part_number, \
                                                                 site=site, serial_number=serial_number, vendor=vendor)
                                    except IntegrityError as db_err:
                                        check_ip = Inventory.objects.values_list('ip', flat=True).get(\
                                            serial_number=serial_number)
                                        if check_ip == ip:
                                            scan_time = str(datetime.now())
                                            Inventory.objects.filter(serial_number=serial_number).update(
                                                timestamp=scan_time,
                                                hostname=hostname,
                                                site=site)
                                        else:
                                            error.append(
                                                str("Error {} for {}".format(str(db_err).split('\n')[1], check_ip)))
                                            ScanLog.objects.create(ip=ip,
                                                                   log="Error scanning node {}. {} for {}".format( \
                                                                       ip, str(db_err).split('\n')[1], check_ip))
                                        pass
            except SSHError as e:
                error.append("NETCONF test - Failed")
                ScanLog.objects.create(ip=ip,
                                       log="Error: NETCONF test - Failed {}".format(e))

    #   elif tvendor=='Cisco IOS':
    #   elif tvendor=='Cisco IOS-XE':
    #   elif tvendor=='ArubaOS' or tvendor =='Aruba':

        else:
            error.append(str("Netconf error - unsupported vendor"))

  # get all objects older than 120 seconds for this ip that weren't update during a scan and delete
  # usecase - module was taken out from chassis
    # TODO check timestamp during the first time creation !!!
    time_threshold = datetime.now() - timedelta(seconds=120)
    if Inventory.objects.filter(timestamp__lte=time_threshold, ip=ip):
  #     Inventory.objects.filter(timestamp__lte=time_threshold, ip=ip).delete()
        Inventory.objects.filter(timestamp__gte=time_threshold, ip=ip).delete()
        Inventory.objects.filter(timestamp__gte=time_threshold, ip=ip).delete()
        print('Deleted')

    if error:
        sresult.append('Errors occurred during the scan - see ScanLog for details.')
    else:
        sresult.append('Scan and DB update - done.')
    return(sresult)