from django.http import HttpResponseRedirect
import os, requests
from .forms import *
from .models import *
from . import getinventory, nodes, reports, main_report, inventorylog
from django.contrib.auth.hashers import make_password
from django.db.models import Count
from django.shortcuts import redirect, render
from django.core.cache import cache
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required

from django.http import HttpResponseServerError
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist

# !!! TODO warehouse ---> all revoked hw placed to warehouse (same location but + warehouse = 'yes' field to sort) !!!
# TODO location!!! change site -> location
# TODO user permissions - done for node delete!!!
# TODO what if the list of hw url will be too long - wrap it to the next column or do collapse list?
## collapse example:  https://getbootstrap.com/docs/5.1/components/collapse/

def home(request):

    result=[]
    scanip=[]     # list of ip for scan
    tcount=''

    # nodes scan
    if request.method == 'POST' and 'runscan' in request.POST:
        form = Invout(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('hostname') != 'all':
                hostname = form.cleaned_data.get('hostname')
                scanip=Inventory.objects.filter(hostname=hostname).values_list('ip', flat=True).distinct()
                result = getinventory.sys_hardware(scanip)
            elif form.cleaned_data.get('ip') != 'all':
                ip = form.cleaned_data.get('ip')
                scanip.append(ip)
                result = getinventory.sys_hardware(scanip)
            elif form.cleaned_data.get('site') != 'all':
                site = form.cleaned_data.get('site')
                scanip = Inventory.objects.filter(site=site).values_list('ip', flat=True).distinct()
                result = getinventory.sys_hardware(scanip)
            elif form.cleaned_data.get('description') != 'all':
                result.append('Note: Scan can be performed by hostname, IP, site, vendor or for all (all nodes in system)')
            elif form.cleaned_data.get('serial_number'):
                result.append('Note: Scan can be performed by hostname, IP, site, vendor or for all (all nodes in system)')
            elif form.cleaned_data.get('vendor') != 'all':
                vendor = form.cleaned_data.get('vendor')
                scanip = Inventory.objects.filter(vendor=vendor).values_list('ip', flat=True).distinct()
                result = getinventory.sys_hardware(scanip)
            else:
                #TODO warning notification about scan all nodes (for big environment)
                scanip = Inventory.objects.values_list('ip', flat=True).distinct()
                result = getinventory.sys_hardware(scanip)

 # Total count of items per module:
   # view if a module was selected (via url in total count form):
    if 'description' in request.session:
        description = request.session['description']
        summ = Inventory.objects.filter(description=description).values().order_by('-hostname')
        count = Inventory.objects.all().values('description').annotate(total=Count('description')).order_by()
        del request.session['description']
        # set per-model search result to cache to use it for csv download.
        cache.set('report_summ', summ)

    # view if a hostname was selected (via hostname url):
 #   elif 'hostname' in request.session:
 #       hostname = request.session['hostname']
 #       summ = Inventory.objects.filter(hostname=hostname).values().order_by('-hostname')
 #       count = Inventory.objects.filter(hostname=hostname).values('description').annotate( \
 #           total=Count('description')).order_by()
 #       del request.session['hostname']
        # set per-model search result to cache to use it for csv download.
 #       cache.set('report_summ', summ)

   # general view and count for all inventory items:
    else:
        if Inventory.objects.order_by('hostname'):
            summ = Inventory.objects.order_by('-hostname')
            count = Inventory.objects.all().values('description').annotate(total=Count('description')).order_by()
            tcount=Inventory.objects.all().values('description').count()
        else:
            summ=''
            count=[]
            tcount=''
   # search
    if request.method == 'POST' and 'search' in request.POST:
    #    cache.clear('report_summ')
        cache.delete('report_summ')
        form = Invout(request.POST)
        summ,count,tcount,result = main_report.search(form)

   # download csv report
    if request.method == 'POST' and 'download' in request.POST:
        response=main_report.report_download(summ)
        return response

    form = Invout()
    return render(request, "home.html", {
                                         'title': 'Inventory system',
                                         'summ':summ,
                                         'form': form,
                                         'result':result,
                                         'count':count,
                                         'tcount':tcount,
                                         })
def allnodes(request):
    msg = ''

    if request.method == 'POST' and 'add' in request.POST:
        form = Setnode(request.POST)
        msg = nodes.add(form)

    scan = []     # last scan for each IP - list of dicts
    tresult = []  # test results
    tid=''        # id of tested node
    if 'node_test' in request.session:
        tid = request.session['node_test'] # get id of tested node
        del request.session['node_test']
        tresult = nodes.test(tid)

    if 'nodescan_ip' in request.session:
        scanip=[]
        tid = request.session['nodescan_id']
        scanip.append(Nodes.objects.values_list('ip', flat=True).get(id=tid))
        del request.session['nodescan_ip']
        tresult = getinventory.sys_hardware(scanip)

    for ip in Nodes.objects.all().values('ip'):
        scan_node = {}
        scan_node['ip'] = ip['ip']
        for scanid in Nodes.objects.filter(ip=scan_node['ip']).values('id'):
            scan_node['id'] = scanid['id']
            if scanid['id'] == tid:      # if node was just tested - add test results
                scan_node['tresult'] = tresult
        # get hostname
        if Inventory.objects.filter(ip=scan_node['ip']).values('hostname').exists():
            scan_node['hostname'] = Inventory.objects.filter(ip=scan_node['ip']).values('hostname').first()['hostname']

        if Inventory.objects.filter(ip=ip['ip']).exists():
            for lastscan in Inventory.objects.filter(ip=scan_node['ip']).values('timestamp').distinct('timestamp'):
                scan_node['lastscan'] = lastscan['timestamp']
        else:
            scan_node['lastscan'] = 'Never'
        scan.append(scan_node)
    form = Setnode()  # TODO set a single form with Edit node
    return render(request, "nodes.html", {'title': 'Nodes',
                                           'form': form,
                                           'msg': msg,
                                           'scan':scan,
                                           'tresult':tresult,
                                           })

@permission_required('Can delete nodes', raise_exception=True)
def NodeDelete(request,id):
    msg=''
    status=''
    for node in Nodes.objects.filter(id=id).values():
        ip= node['ip']
    if request.method == 'POST' and 'delete' in request.POST:
        status, msg = nodes.delete(ip)

    return render(request, "delete.html", {'title': 'Delete node',
                                           'ip': ip,
                                           'msg': msg,
                                           'status':status
                                            })

def NodeEdit(request,id):
    msg=[]
 #   form = Editnode()
    summ = Nodes.objects.filter(id=id).values()
    ip=Nodes.objects.values_list('ip', flat=True).get(id=id)
    hostname=Inventory.objects.filter(ip=ip).values('hostname').distinct('hostname')
    form = Editnode(request.POST)   # TODO set a single form with Edit node
    if request.method == 'POST' and 'edit' in request.POST:
        msg = nodes.edit(id, form)
    form = Editnode()   # TODO set a single form with Edit node
    return render(request, "edit.html", {'title': 'Edit node',
                                           'form': form,
                                           'summ': summ,
                                           'hostname': hostname,
                                           'msg': msg,
                                           })

def NodeTest(request, id):
    request.session['node_test'] = id
    return redirect(allnodes)

def NodeScan(request, id):
    request.session['nodescan_id'] = id
    ip=Nodes.objects.values_list('ip', flat=True).get(id=id)
    request.session['nodescan_ip'] = ip
    return redirect(allnodes)

def modules(request, description):
    # TODO perform search for HW description by site if site was selected via form - how to send +1 argument via url?
    #   site variable must be saved in session['site']
    #   example:
    #   path('virtual-chassis/<int:pk>/journal/', ObjectJournalView.as_view(), name='virtualchassis_journal', kwargs={'model': VirtualChassis}),
 # provides search by selected appropriate urls on main page
    request.session['description'] = description
    return redirect(home)

def report(request):
    summ=reports.glbreport()
    if request.method == 'POST' and 'download' in request.POST:
        response=reports.glbreport_download()
        return response
    return render(request, "report.html", {
        'title': 'Report',
        'summ': summ,
    })

def scanlog(request):
    summ_log=ScanLog.objects

    return render(request, "scanlog.html", {
                          'title': 'ScanLog',
                          'summ_log': summ_log,
    })

def invlog(request):
  #  summ_log=InventoryLog.objects.order_by('-timestamp')
    summ_log=InventoryLog.objects.order_by('-timestamp')

    # TODO result output --> if hw was withdrawn from a node --> add a record
    # TODO --> TEST move hw to another node !!!
    # search
    if request.method == 'POST' and 'search' in request.POST:
    #    cache.clear()
        form = Inventorylog(request.POST)
        summ_log, result = inventorylog.search(form)

    # download csv report
    elif request.method == 'POST' and 'download' in request.POST:
        response = inventorylog.inv_download(summ_log)
        return response
    form = Inventorylog()
    return render(request, "invlog.html", {
                          'title': 'Inventory Log',
                          'form': form,
                          'summ_log': summ_log,
    })

def stats(request):
    summ=reports.glbreport()
    mcount = Inventory.objects.all().values('description').annotate(total=Count('description')).order_by()
    vcount = Inventory.objects.all().values('vendor').annotate(total=Count('vendor')).order_by()
    labels=[]
    data=[]
    vendor=[]
    vendorcount=[]
    for item in mcount:
        labels.append(item['description'])
        data.append(item['total'])
    for item in vcount:
        vendor.append(item['vendor'])
        vendorcount.append(item['total'])

    return render(request, "stats.html", {
                          'title': 'Licenses',
                          'labels': labels,
                           'data': data, # TODO: change to hw_descr
                           'vendor': vendor,
                           'vendorcount': vendorcount,
    })


def about(request):
    return render(request, "about.html", {
                          'title': 'About',
    })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')

def handler404(request, exception):
    return render(request, "404.html", {
                            'title': 'Page not found',
    })

#def handler500(request):
#    return render(request, "500.html", {
#                            'title': 'Bad Request Error',
#    })

def server_error(request, template_name='500.html'):
    """
    500 error handler.

    :template: :file:`500.html`
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        if template_name != '500.html':
            # Reraise if it's a missing custom template.
            raise
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    return HttpResponseServerError(template.render(request=request))