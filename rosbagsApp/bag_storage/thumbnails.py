from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import rosbags.rosbag2 as rb
from django.utils.text import slugify
from rosbags.serde import deserialize_cdr
from rosbags.typesys import get_types_from_msg, register_types


def create_thumbnail_spatz(bag_dir: Path, reader: rb.Reader, connection: rb.reader.Connection) -> set[str]:
    """
    This is just an example of how thumbnail generation might work. We still have to figure out how (if) we want to
    provide custom message types and thumbnail generators. The next step however will be to implement this for well
    known, useful types (sensor_msgs/Image for example).

    :return: List of filenames of generated thumbnails
    """
    assert (connection.msgtype == "spatz_interfaces/msg/Spatz")
    print("Creating thumbs")
    register_types(get_types_from_msg("""
            float64 width
            float64 length
            float64 origin_x
            float64 track_length
            float64 track_width
            float64 mass
            
            float64 max_steering_angle
            
            float64 dist_cog_to_front_axle
            float64 dist_cog_to_rear_axle
            float64 dist_cam_origin_x
            """, "spatz_interfaces/msg/SystemParams"))

    register_types(get_types_from_msg("""
            std_msgs/Header header
            
            geometry_msgs/Point pose # x, y, psi (yaw angle in rad)
            geometry_msgs/Point velocity # x, y velocity in global coordinates
            geometry_msgs/Point acceleration # acceleration (in vehicle coordinates) without gravity
            float64 d_psi # angular velocity
            
            # Sensors
            float64 laser_front
            float64 steer_angle_front # estimated steering angle of the front axle in rad (left is positive)
            float64 steer_angle_rear # estimated steering angle of the rear axle in rad (left is positive)
            
            bool light_switch_rear
            
            float64 integrated_distance
            
            SystemParams system_params
            """, "spatz_interfaces/msg/Spatz"))
    xs = np.zeros((connection.msgcount,))
    ys = np.zeros((connection.msgcount,))
    for i, (_, timestamp, rawdata) in enumerate(reader.messages([connection])):
        msg = deserialize_cdr(rawdata, connection.msgtype)
        xs[i] = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec * 1e-9)
        ys[i] = msg.pose.x
    matplotlib.use("Agg")
    fig: plt.Figure
    ax: plt.Axes
    fig, ax = plt.subplots()
    ax.plot(xs, ys)
    thumb_dir = bag_dir / "thumbnails"
    thumb_dir.mkdir(exist_ok=True)
    thumb_name = slugify(connection.topic) + ".png"
    fig.savefig(thumb_dir / thumb_name)
    return {thumb_name}
