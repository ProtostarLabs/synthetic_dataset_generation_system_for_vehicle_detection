import bpy
from mathutils import Vector


def create_coco(data, image_id, category_id, bbox):
    """
    Adds the coco annotation for the given bounding box to
    the given coco data dictionary.
    """
    data["annotations"].append({
        "id": image_id,
        "image_id": image_id,
        "category_id": category_id,
        "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
        "area": bbox[2] * bbox[3],
        "iscrowd": 0,
        "segmentation": []
    })
    return data


def get_co_in_pixels(scene, co_2d):
    """
    Transforms coordinates in the camera space
    to the pixel format.
    """
    return [
        round(co_2d[0] * get_render_scale(scene)[0]),
        round(co_2d[1] * get_render_scale(scene)[1]),
    ]


def get_render_scale(scene):
    """
    Returns the factor used for calculating dimensions
    on the scene in pixel domain.
    """
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
        int(scene.render.resolution_x * render_scale),
        int(scene.render.resolution_y * render_scale),
    )
    return [
        render_size[0],
        render_size[1]
    ]


def get_bounding_box_coordinates(obj):
    """ 
    Returns the rotated bounding box world coordinates of
    the given object.
    """
    box = obj.bound_box
    # World Space
    p = [obj.matrix_world @ Vector(corner) for corner in box]
    # Now the box is 3D but we want to take only the top/bottom box
    del p[::2]
    return p


def get_all_cars_bounding_boxes():
    """
    Returns an array with the boudning boxes of all the
    car objects on the scene.
    """
    cars_bounding_boxes = []
    for obj in bpy.data.objects:
        if obj.name.startswith("Car"):
            cars_bounding_boxes.append(get_bounding_box_coordinates(obj))
    return cars_bounding_boxes


def get_all_tractors_bounding_boxes():
    """
    Returns an array with the boudning boxes of all the
    car objects on the scene.
    """
    tractors_bounding_boxes = []
    for obj in bpy.data.objects:
        if obj.name.startswith("Tractor"):
            tractors_bounding_boxes.append(get_bounding_box_coordinates(obj))
    return tractors_bounding_boxes


def return_coco_box(box_x, box_y, scene):
    """
    Returns the bounding box from the given lists of
    x and y coordinates.
    """
    x = min(box_x)
    y = max(box_y)
    width = max(box_x) - min(box_x)
    height = max(box_y) - min(box_y)

    x_px = get_co_in_pixels(scene, [x, y])[0]
    y_px = get_render_scale(scene)[1] - get_co_in_pixels(scene, [x, y])[1]
    width_px = get_co_in_pixels(scene, [width, height])[0]
    height_px = get_co_in_pixels(scene, [width, height])[1]

    return [x_px, y_px, width_px, height_px]


def return_yolo_box(box_x, box_y):
    """
    Returns the bounding box in yolo format from the given
    lists of x and y coordinates.
    """
    x = (min(box_x) + max(box_x)) / 2
    y = 1 - (min(box_y) + max(box_y)) / 2
    width = max(box_x) - min(box_x)
    height = max(box_y) - min(box_y)

    return x, y, width, height
