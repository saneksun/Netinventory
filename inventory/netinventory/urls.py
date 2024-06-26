"""inventory URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include, re_path
from netinventory import views as netinventory_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", netinventory_views.home, name="home"),
    re_path(r"^description/(?P<description>[-a-zA-Z0-9_/]+)", netinventory_views.modules, name="module_filter"),
    re_path(r"^hostname/(?P<hostname>[-a-zA-Z0-9_/]+)", netinventory_views.nodesfilter, name='nodes_filter'),
    re_path(r"^nodes/details/(?P<hostname>[-a-zA-Z0-9_/]+)", netinventory_views.nodedetails, name='node_details'),
    path("nodes/", netinventory_views.allnodes, name="nodes"),
    path("report/", netinventory_views.report, name="report"),
    path("delete/<int:id>/", netinventory_views.NodeDelete, name="delete"),
    path("edit/<int:id>/", netinventory_views.NodeEdit, name="edit"),
    path("nodes/<int:id>/", netinventory_views.NodeTest, name="test"),
    path("scan/<int:id>/", netinventory_views.NodeScan, name="scan"),
    path("scanlog/", netinventory_views.scanlog, name="scanlog"),
    path("invlog/", netinventory_views.invlog, name="invlog"),
    path("stats/", netinventory_views.stats, name="stats"),
    path("about/", netinventory_views.about, name="about"),
    path("logout/", netinventory_views.logout_view, name="logout"),
            ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler500 = netinventory_views.server_error
