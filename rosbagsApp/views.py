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
def detail(request, bag_path: str):
    bs = BagStorage()
    context = {'bag': bs.find_by_path(Path(bag_path)),
               'local_mount_prefix': rosbagsApp.settings.ROSBAG_MOUNT_PATH}
    return render(request, "rosbagsApp/detail_view.html", context)


@login_required
def thumbnail(request, bag_path: str, thumb_name: str):
    bag = BagStorage().find_by_path(Path(bag_path))
    path = os.path.join(bag.path, "thumbnails", thumb_name)
    path = os.path.realpath(path)
    if Path(os.path.commonpath([path, bag.path])) != bag.path:
        return HttpResponseBadRequest(f"Thumbnail path outside bag directory: {path}")
    return FileResponse(open(path, 'rb'))


def generate_thumbnails(request):
    bag_path = request.GET.get("bag_path", None)
    if bag_path is None:
        return HttpResponseBadRequest("Parameter bag_path is required.")
    bs = BagStorage()
    bag = bs.find_by_path(Path(bag_path))
    if bag is None:
        return HttpResponseBadRequest(f"Bag with path \"{bag_path}\" is not found.")

    bag.generate_thumbnails()

    return HttpResponse("done!")
