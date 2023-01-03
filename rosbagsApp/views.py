import json
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

import rosbagsApp.settings
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
    context = {'bag': bs.find(bag_name),
               'local_mount_prefix': rosbagsApp.settings.ROSBAG_MOUNT_PATH}
    return render(request, "rosbagsApp/detail_view.html", context)


@login_required
def thumbnail(request, bag_name: str, thumb_name: str):
    bag = BagStorage().find(bag_name)
    path = os.path.join(bag.path, "thumbnails", thumb_name)
    path = os.path.realpath(path)
    if Path(os.path.commonpath([path, bag.path])) != bag.path:
        return HttpResponseBadRequest(f"Thumbnail path outside bag directory: {path}")
    return FileResponse(open(path, 'rb'))


def generate_thumbnails(request):
    bag_name = request.GET.get("bag_name", None)
    if bag_name is None:
        return HttpResponseBadRequest("Parameter bag_name is required.")
    bs = BagStorage()
    bag = bs.find(bag_name)
    if bag is None:
        return HttpResponseBadRequest(f"Bag with name\"{bag_name}\" is not found.")

    bag.generate_thumbnails()

    return HttpResponse("done!")
