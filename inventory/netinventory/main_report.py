
from .forms import *
from django.db.models import Count
from django.core.cache import cache
from django.http import HttpResponse
from datetime import datetime
import csv

# for search and report download from the main page
report_summ = ''


def search(form):
    tcount = ''
    count=''
    result = []
    global report_summ
    summ = Inventory.objects.order_by('-hostname')
    if form.is_valid():
        # filter by site
        if form.cleaned_data.get('site') != 'all':
            site = form.cleaned_data.get('site')
            # additional search by hw description
            if form.cleaned_data.get('description') != 'all':
                description = form.cleaned_data.get('description')
                summ = Inventory.objects.filter(site=site, description=description).values().order_by('-hostname')
                count = Inventory.objects.filter(site=site, description=description).values('description').annotate(
                    total=Count('description')).order_by()
                tcount = ''
                report_summ = summ
            # additional search by vendor
            elif form.cleaned_data.get('vendor') != 'all':
                vendor = form.cleaned_data.get('vendor')
                summ = Inventory.objects.filter(site=site,vendor=vendor).values().order_by('-hostname')
                count = Inventory.objects.filter(site=site,vendor=vendor).values('description').annotate(
                    total=Count('description')) \
                    .order_by()
                tcount = ''
                report_summ = summ
            else:
                summ = Inventory.objects.filter(site=site).values().order_by('-hostname')
                count = Inventory.objects.filter(site=site).values('description').annotate(total=Count('description')) \
                    .order_by()
                tcount = Inventory.objects.filter(site=site).values('description').count()
                report_summ = summ

        elif form.cleaned_data.get('hostname') != 'all':
            hostname = form.cleaned_data.get('hostname')
            summ = Inventory.objects.filter(hostname=hostname).values().order_by('-hostname')
            count = Inventory.objects.filter(hostname=hostname).values('description').annotate(
                total=Count('description')) \
                .order_by()
            tcount = Inventory.objects.filter(hostname=hostname).values('description').count()
            report_summ = summ
        elif form.cleaned_data.get('description') != 'all':
            description = form.cleaned_data.get('description')
            summ = Inventory.objects.filter(description=description).values().order_by('-hostname')
            count = Inventory.objects.filter(description=description).values('description').annotate(
                total=Count('description')) \
                .order_by()
            tcount = ''
            report_summ = summ
        elif form.cleaned_data.get('serial_number'):
            serial_number = form.cleaned_data.get('serial_number')
            summ = Inventory.objects.filter(serial_number=serial_number).values().order_by('-hostname')
            count = ''
            tcount = ''
            report_summ = summ
        elif form.cleaned_data.get('vendor') != 'all':
            vendor = form.cleaned_data.get('vendor')
            summ = Inventory.objects.filter(vendor=vendor).values().order_by('-hostname')
            count = Inventory.objects.filter(vendor=vendor).values('description').annotate(total=Count('description')) \
                .order_by()
            tcount = ''
            report_summ = summ
        elif form.cleaned_data.get('ip') != 'all':
            ip = form.cleaned_data.get('ip')
            if Inventory.objects.filter(ip=ip).values().order_by('-hostname'):
                summ = Inventory.objects.filter(ip=ip).values().order_by('-hostname')
                count = Inventory.objects.filter(ip=ip).values('description').annotate(total=Count('description')) \
                .order_by()
                tcount = ''
                report_summ = summ
            else:
                result.append('Nothing found for selected IP.')
        else:  # Search by all
            summ = Inventory.objects.order_by('-hostname')
            count = Inventory.objects.all().values('description').annotate(total=Count('description')).order_by()
            tcount = Inventory.objects.all().values('description').count()
    return(summ,count,tcount,result)

def report_download(summ):
    global report_summ
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report_{}.csv"'.format(
        str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))
    writer = csv.writer(response, delimiter=',')
    writer.writerow([''])
    writer.writerow(['Creation time: {}'.format(str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))])
    writer.writerow([''])
    writer.writerow(['Hostname', 'IP', 'Vendor', 'Hardware', 'Serial number', 'Part number', 'Site', 'Last update'])
    # Download csv per search results via form
    if report_summ:
        summ=report_summ
        for summ in summ:
            writer.writerow([
                summ['hostname'],
                summ['ip'],
                summ['vendor'],
                summ['description'],
                summ['serial_number'],
                summ['part_number'],
                summ['site'],
                summ['timestamp'],
                ])
    # Download csv per search results via model count in total count urls field
    elif cache.get('report_summ'):
        summ=cache.get('report_summ')
        for summ in summ:
            writer.writerow([
                summ['hostname'],
                summ['ip'],
                summ['vendor'],
                summ['description'],
                summ['serial_number'],
                summ['part_number'],
                summ['site'],
                summ['timestamp'],
                ])
    # download csv for all inventory items
    else:
      #  summ = Inventory.objects.order_by('-hostname')
        for summ in summ:
            writer.writerow([
                summ.hostname,
                summ.ip,
                summ.vendor,
                summ.description,
                summ.serial_number,
                summ.part_number,
                summ.site,
                summ.timestamp,
                ])
    return response