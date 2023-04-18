
from .forms import *
from django.db.models import Count
from django.core.cache import cache
from django.http import HttpResponse
from datetime import datetime
import csv

log_sum = ''


def search(form):
    result = []
    global log_sum
    log_sum=''
    sum_log = InventoryLog.objects
    if form.is_valid():
        # filter by site
        if form.cleaned_data.get('site') != 'all':
            site = form.cleaned_data.get('site')
            # additional search by hw name
            if form.cleaned_data.get('name') != 'all':
                name = form.cleaned_data.get('name')
                sum_log = InventoryLog.objects.filter(site=site, name=name).values().order_by('-hostname')
                log_sum = sum_log
            else:
                sum_log = InventoryLog.objects.filter(site=site).values().order_by('-hostname')
                log_sum = sum_log
        elif form.cleaned_data.get('hostname') != 'all':
            hostname = form.cleaned_data.get('hostname')
            sum_log = InventoryLog.objects.filter(hostname=hostname).values().order_by('-hostname')
            log_sum = sum_log
        elif form.cleaned_data.get('name') != 'all':
            name = form.cleaned_data.get('name')
            sum_log = InventoryLog.objects.filter(name=name).values().order_by('-hostname')
            log_sum = sum_log
        elif form.cleaned_data.get('serial_number'):
            serial_number = form.cleaned_data.get('serial_number')
            sum_log = InventoryLog.objects.filter(serial_number=serial_number).values().order_by('-timestamp')
            log_sum = sum_log
        elif form.cleaned_data.get('ip') != 'all':
            ip = form.cleaned_data.get('ip')
            if InventoryLog.objects.filter(ip=ip).values().order_by('-hostname'):
                sum_log = InventoryLog.objects.filter(ip=ip).values().order_by('-hostname')
                log_sum = sum_log
            else:
                result.append('Nothing found for selected IP.')

        else:  # Search by all
            sum_log = InventoryLog.objects.order_by('-timestamp')

    return (sum_log, result)


def inv_download(sum):
    global log_sum
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_log_{}.csv"'.format(
        str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))
    writer = csv.writer(response, delimiter=',')
    writer.writerow([''])
    writer.writerow(['Creation time: {}'.format(str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))])
    writer.writerow([''])
    writer.writerow(['Time', 'NodeIP', 'Hostname', 'Hardware', 'Serial number', 'Site', 'Description'])
    # search output
    if log_sum:
        for sum in log_sum:
            writer.writerow([
                sum['timestamp'],
                sum['ip'],
                sum['hostname'],
                sum['name'],
                sum['serial_number'],
                sum['site'],
                sum['log_description'],
                ])
    # general view
    else:
        for sum in sum:
            writer.writerow([
                sum.timestamp,
                sum.ip,
                sum.hostname,
                sum.name,
                sum.serial_number,
                sum.site,
                sum.log_description,
                ])

    return response

