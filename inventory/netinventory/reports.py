
from .forms import *
from django.db.models import Count
from django.http import HttpResponse
from datetime import datetime
import csv

def glbreport():
    global summ
    summ=[]
 #   list of sites without dublicate - .distinct('site'):
    for site in Inventory.objects.all().values('site').distinct('site'):
        sites={}
        sites['site'] = site
        sites['vendor'] = []
        for vendor in Inventory.objects.filter(site=site['site']).values('vendor').distinct('vendor'):
            count = Inventory.objects.filter(site=site['site'], vendor=vendor['vendor']).values('description') \
            .annotate(total=Count('description')).order_by()
            r={}
            r['vendor'] = vendor['vendor']
            r['count'] = count
            sites['vendor'].append(r)
        summ.append(sites)
    return (summ)

def glbreport_download():
    global summ
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="general_report_{}.csv"'.format(
        str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))
    writer = csv.writer(response, delimiter=',')
    writer.writerow([''])
    writer.writerow(['Creation time: {}'.format(str(datetime.now().strftime("%Y-%m-%d_%H%M%S")))])
    writer.writerow([''])
    writer.writerow(['Hardware', 'Count'])
    for summ in summ:
        writer.writerow([
            summ['site']['site']
        ])
        for vendor in summ['vendor']:
            writer.writerow([
                vendor['vendor']
            ])
            for count in vendor['count']:
                writer.writerow([
                    count['description'],
                    count['total']
                ])
    return response