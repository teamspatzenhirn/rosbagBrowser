import json
import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseBadRequest
from django.shortcuts import render

from rosbagsApp.bag_storage.storage import BagStorage, ROSBag


@login_required
def index(request):
    return render(request, "rosbagsApp/index.html")


@login_required
def list_view(request):
    bs = BagStorage()
    bags: list[ROSBag] = list(bs)
    bags.sort(key=lambda b: b.recording_date, reverse=True)

    bags_json = json.dumps([b.json() for b in bags])
    context = {'bags': bags_json}

    return render(request, "rosbagsApp/list.html", context)


@login_required
def detail(request, bag_name: str):
    bs = BagStorage()
    context = {'bag': bs.find(bag_name)}
    return render(request, "rosbagsApp/detail_view.html", context)


@login_required
def thumbnail(request, bag_name: str, thumb_name: str):
    bag = BagStorage().find(bag_name)
    path = os.path.join(bag.path, "thumbnails", thumb_name)
    path = os.path.realpath(path)
    if os.path.commonpath([path, bag.path]) != bag.path:
        return HttpResponseBadRequest(f"Thumbnail path outside bag directory: {path}")
    return FileResponse(open(path, 'rb'))
