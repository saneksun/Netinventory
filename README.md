# NetInventory

NetInventory is a tool that is scanning network devices in order to collect hardware inventory information (modules names, part-numbers, serial numbers) using standard SNMP (v1, v2c) and NETCONF (SSH port 830) protocols.

![image](https://github.com/saneksun/Netinventory/assets/39739673/2e1b5e68-7b73-4869-b65a-96bcb953f432)

The collected inventory can be saved as csv report.

## Supported platforms:
- Juniper JunOS
- Cisco IOS-XR
  
## User permissions

The following permissions are available in NetInventory and can be used via Admin panel (for superuser):
- Can add nodes
- Can change nodes
- Can delete nodes

## Prerequisites
- Django
- PostgreSQL

