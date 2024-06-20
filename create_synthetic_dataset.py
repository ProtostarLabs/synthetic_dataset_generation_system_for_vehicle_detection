import json
import math
import os
import random
import sys

import bpy
import bpy_extras
import bmesh
import geopandas as gpd
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

sys.path.append(os.path.dirname(__file__))
from config import *
from annotation_tools import *


iteration = 0

def random_points_in_polygon(n, max_x, max_y):
    """
    Returns arrays of x and y coordinates with the size n
    and inside polygon bounding box.
    """
    x = np.random.uniform(-max_x, max_x, n)
    y = np.random.uniform(-max_y, max_y, n)
    return x, y


def import_map_and_roads():
    """
    Loads some blend file that has map saved with needed
    emission shader and highways data.
    """
    current_map_index = random.randint(1, LANDS_MODELS_COUNT)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(
        MAIN_PATH, "Lands", str(current_map_index) + ".blend"))


def add_farm_vehicles(max_x, max_y):
    """
    Adds farm vehicles, such as tractors and havesters, to the farmland
    if there is any farmland available.
    """
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer

    try:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects["Areas:landuse"].select_set(True)
        view_layer.objects.active = bpy.data.objects["Areas:landuse"]
        farmland_vertices = []

        for vert in bpy.context.object.data.vertices:
            if (bpy.context.object.vertex_groups["Tag:landuse=farmland"].index
                in [i.group for i in vert.groups]):
                farmland_vertices.append((vert.co.x, vert.co.y))

        gdf_poly = gpd.GeoDataFrame(
            index=["myPoly"], geometry=[Polygon(farmland_vertices)])

        df = pd.DataFrame()
        df["points"] = list(zip(
            random_points_in_polygon(NUMBER_OF_FARM_VEHICLES, max_x, max_y)[0],
            random_points_in_polygon(NUMBER_OF_FARM_VEHICLES, max_x, max_y)[1]))
        df["points"] = df["points"].apply(Point)
        gdf_points = gpd.GeoDataFrame(df, geometry="points")

        s_join = gpd.tools.sjoin(
            gdf_points, gdf_poly, predicate="within", how="left")

        # Keep points in "myPoly"
        points_in_farmland = gdf_points[s_join.index_right=="myPoly"]

        for i in range(0, len(points_in_farmland)):
            bpy.ops.import_scene.fbx(filepath = os.path.join(
                MAIN_PATH, "Vehicles", "Tractors", "Tractor" +
                str(random.randint(1, TRACTOR_MODELS_COUNT)) + ".fbx"))

            new_vehicle_obj = bpy.context.selected_objects[0]
            scene.cursor.location = (
                points_in_farmland.iloc[i].points.x,
                points_in_farmland.iloc[i].points.y, 0)
            new_vehicle_obj.matrix_world.translation = scene.cursor.location
            new_vehicle_obj.rotation_mode = "XYZ"
            new_vehicle_obj.rotation_euler = (0, 0, random.uniform(0, math.pi))

        to_place_on_roads = 1/2

    except KeyError:
        to_place_on_roads = 1

    farm_vehicles_count = 0
    while farm_vehicles_count < NUMBER_OF_CARS*to_place_on_roads:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects["Ways:highway"].select_set(True)
        view_layer.objects.active = bpy.data.objects["Ways:highway"]

        bpy.ops.object.mode_set(mode="EDIT")

        bm = bmesh.from_edit_mesh(bpy.data.objects["Ways:highway"].data)

        bm.edges.ensure_lookup_table()
        edge_vertices = get_random_edge_vertices(bm, max_x, max_y)
        location_and_rotation = get_point_on_line(edge_vertices, max_x, max_y)

        scene.cursor.location = location_and_rotation[0]

        bpy.ops.import_scene.fbx(filepath = os.path.join(
            MAIN_PATH, "Vehicles", "Tractors", "Tractor" +
            str(random.randint(1, TRACTOR_MODELS_COUNT)) + ".fbx"))
        new_vehicle_obj = bpy.context.selected_objects[0]
        new_vehicle_obj.matrix_world.translation = scene.cursor.location
        new_vehicle_obj.location = location_and_rotation[0]
        new_vehicle_obj.rotation_mode = "XYZ"
        new_vehicle_obj.rotation_euler = (
            0, 0, location_and_rotation[1] + math.pi*random.randint(0,1))
        farm_vehicles_count += 1

        for obj in bpy.data.objects:
            if obj.name.startswith("Car") or obj.name.startswith("Tractor"):
                if do_objects_overlap(new_vehicle_obj, obj):
                    bpy.ops.object.delete()
                    farm_vehicles_count -= 1
                    break


def add_new_car(max_x, max_y):
    """
    Adds a car model to the scene and positions it
    on the road with correct rotation.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.data.objects["Ways:highway"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Ways:highway"]

    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(bpy.data.objects["Ways:highway"].data)
    #verts = [vert.co for vert in bm.verts]

    bm.edges.ensure_lookup_table()

    edge_vertices = get_random_edge_vertices(bm, max_x, max_y)

    location_and_rotation = get_point_on_line(edge_vertices, max_x, max_y)

    bpy.context.scene.cursor.location = location_and_rotation[0]

    bpy.ops.import_scene.fbx(filepath = os.path.join(
        MAIN_PATH, "Vehicles", "Cars", "Car" +
        str(random.randint(1, CAR_MODELS_COUNT)) + ".fbx"))
    car_obj = bpy.context.selected_objects[0]
    car_obj.matrix_world.translation = bpy.context.scene.cursor.location
    car_obj.rotation_mode = "XYZ"
    car_obj.rotation_euler = (
        0, 0, location_and_rotation[1] + math.pi*random.randint(0,1))

    edit_material(car_obj)

    for obj in bpy.data.objects:
        if obj.name.startswith("Car"):
            # If added car overlaps another one, delete it
            if do_objects_overlap(car_obj, obj):
                bpy.ops.object.delete()
                return 0

    return 1


def do_objects_overlap(obj1, obj2):
    """
    Returns True if the object's bounding boxes are overlapping.
    """
    vert1 = [obj1.matrix_world @ Vector(corner) for corner in obj1.bound_box]
    vert2 = [obj2.matrix_world @ Vector(corner) for corner in obj2.bound_box]
    # Map vertices to 6 faces
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]

    bvh1 = BVHTree.FromPolygons(vert1, faces)
    bvh2 = BVHTree.FromPolygons(vert2, faces)

    return bool(bvh1.overlap(bvh2))


def get_point_on_line(edge_vertices, max_x, max_y):
    """
    Calculate the line equation. Picks a random point on
    the given line. Returns that point and line angle.
    Useful equation: (x-x1)/l = (y-y1)/m = (z-z1)/n.
    """
    #   Pick random x value between x values of vertex 1 and vertex 2
    x = random.uniform(edge_vertices[0].co.x, edge_vertices[1].co.x)

    l = edge_vertices[1].co.x - edge_vertices[0].co.x
    m = edge_vertices[1].co.y - edge_vertices[0].co.y
    n = edge_vertices[1].co.z - edge_vertices[0].co.z

    # Avoid division by zero
    l = 0.1 if l == 0 else l

    a = (x - edge_vertices[0].co.x) / l
    y = a * m + edge_vertices[0].co.y
    z = a * n + edge_vertices[0].co.z

    try:
        slope = ((edge_vertices[1].co.y-edge_vertices[0].co.y)/
                 (edge_vertices[1].co.x-edge_vertices[0].co.x))
    except ZeroDivisionError:
        slope = (edge_vertices[1].co.y-edge_vertices[0].co.y)/0.0001
    angle = math.atan(slope)

    while x > max_x or y > max_y:
        #   Pick random x value between x values of vertex 1 and vertex 2
        x = random.uniform(edge_vertices[0].co.x, edge_vertices[1].co.x)

        l = edge_vertices[1].co.x - edge_vertices[0].co.x
        m = edge_vertices[1].co.y - edge_vertices[0].co.y
        n = edge_vertices[1].co.z - edge_vertices[0].co.z

        # Avoid division by zero
        l = 0.1 if l == 0 else l

        a = (x - edge_vertices[0].co.x) / l
        y = a * m + edge_vertices[0].co.y
        z = a * n + edge_vertices[0].co.z

        try:
            slope = ((edge_vertices[1].co.y-edge_vertices[0].co.y)/
                     (edge_vertices[1].co.x-edge_vertices[0].co.x))
        except ZeroDivisionError:
            slope = (edge_vertices[1].co.y-edge_vertices[0].co.y)/0.0001
        angle = math.atan(slope)

    return (x, y, z), angle


def get_random_edge_vertices(bm, max_x, max_y):
    """
    Selects a radnom road edge and returns the
    vertices of that edge.
    """
    edge = bm.edges[random.randint(0, len(bm.edges)-1)]

    #   Get edge vertices
    edge_vertex_1 = edge.verts[0]
    edge_vertex_2 = edge.verts[1]

    while (
        (abs(edge_vertex_1.co.x) > max_x or abs(edge_vertex_1.co.y) > max_y) and
        (abs(edge_vertex_2.co.x) > max_x or abs(edge_vertex_2.co.y) > max_y)):
        edge = bm.edges[random.randint(0, len(bm.edges)-1)]

        #   Get edge vertices
        edge_vertex_1 = edge.verts[0]
        edge_vertex_2 = edge.verts[1]

    return edge_vertex_1, edge_vertex_2


def edit_material(car_obj):
    """
    Changes the base color of the vehicle.
    """
    color_choice = np.random.choice(
        np.arange(0, len(car_colors), 1), p=car_colors_weights)
    car_material_nodes = car_obj.material_slots[0].material.node_tree.nodes
    car_material_nodes[0].inputs[0].default_value = car_colors[color_choice]


def decide_camera_locations(max_x, max_y):
    """
    Selects random camera locations. Makes sure that
    road is visible on each position to avoid rendering
    empty images with no roads and no cars.
    """
    vertices = bpy.data.objects["Ways:highway"].data.vertices
    camera = bpy.data.objects["Camera"]
    scene = bpy.context.scene
    camera_locations = []
    # for _ in range(0, NUMBER_OF_CAMERAS):
    cameras_added = 0
    while cameras_added < NUMBER_OF_CAMERAS:
        # Add some space to avoid going out of the map

        random_x_location = random.uniform(-max_x+125, max_x-125)
        random_y_location = random.uniform(-max_y+72, max_y-72)

        camera.location[0] = random_x_location
        camera.location[1] = random_y_location

        # camera = bpy.data.objects['Camera']
        # scene = bpy.context.scene
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects["Ways:highway"].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects["Ways:highway"]

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.object.mode_set(mode="OBJECT")

        for vert in vertices:
            co_in_camera = get_co_in_camera_space(scene, camera, vert.co)

            if(co_in_camera[0] >= 0 and co_in_camera[0] <=1 and
                co_in_camera[1] >= 0 and co_in_camera[1] <=1):
                cameras_added += 1
                camera_locations.append(
                    (random_x_location, random_y_location,
                    CAMERA_HEIGHT))
                break

    return camera_locations


def add_sun():
    """
    Adds sun to the scene. Changes sun properties (longitude and latitude)
    to match the ones of the map geo location.
    """
    scene = bpy.context.scene
    world = bpy.data.worlds["World"]

    # Add sun to the scene
    bpy.ops.object.light_add(type="SUN")
    bpy.data.objects["Sun"].data.energy = 5

    scene.sun_pos_properties.latitude = scene["latitude"]
    scene.sun_pos_properties.longitude = scene["longitude"]
    scene.sun_pos_properties.sun_object = bpy.data.objects["Sun"]
    # Set the sun object to the Sun previously added to the scene
    scene.sun_pos_properties.time = 12

    # Make background reflect some light
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9


def add_shadow_catcher():
    """
    Adds a plane that will be used as a shadow catcher - to
    receive and show the shadow while being transparent.
    """
    # Add shadow catcher plane that is as big as the map
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0.1))
    bpy.data.objects["Plane"].scale = [
        bpy.data.objects["EXPORT_GOOGLE_SAT_WM"].dimensions.x,
        bpy.data.objects["EXPORT_GOOGLE_SAT_WM"].dimensions.y,
        1]

    # Make it a shadow catcher
    bpy.data.objects["Plane"].is_shadow_catcher = True
    # Remove ray visibility for diffuse and glossy
    bpy.data.objects["Plane"].visible_diffuse = False
    bpy.data.objects["Plane"].visible_glossy = False
    # Make it transparent
    bpy.context.scene.render.film_transparent = True

    bpy.ops.render.render()


def prepare_compositor():
    """
    Set up compositor nodes. Setup containes Alpha Over node to connect shadow
    catcher and the background scene. Also includes nodes to match the car
    resolution to the rest of the map.
    """
    bpy.ops.render.render()
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    render_layers_node = tree.nodes["Render Layers"]
    composite_node = tree.nodes["Composite"]
    viewer_node = tree.nodes.new(type="CompositorNodeViewer")
    image_node = tree.nodes.new(type="CompositorNodeImage")
    hue_sat_node = tree.nodes.new(type="CompositorNodeHueSat")
    exposure_node = tree.nodes.new(type="CompositorNodeExposure")
    alpha_over_node = tree.nodes.new(type="CompositorNodeAlphaOver")
    blur1_node = tree.nodes.new(type="CompositorNodeBlur")
    blur2_node = tree.nodes.new(type="CompositorNodeBlur")
    scale1_node = tree.nodes.new(type="CompositorNodeScale")
    scale2_node = tree.nodes.new(type="CompositorNodeScale")
    pixelate_node = tree.nodes.new(type="CompositorNodePixelate")
    hue_sat_node.inputs[2].default_value = random.uniform(0.9, 1.0) #0.9
    exposure_node.inputs[1].default_value = random.uniform(1.0, 1.3) #1.3

    # This blurring and scaling reduce the quality of rendered vehicles
    # so that they would match the limited map resolution
    blur1_node.size_x = round(render_resolution[0]/341)
    blur1_node.size_y = round(render_resolution[1]/341)
    blur2_node.size_x = round(render_resolution[0]/1024)
    blur2_node.size_y = round(render_resolution[1]/1024)
    blur1_node.filter_type = "CATROM"
    blur2_node.filter_type = "CATROM"
    scale1_node.inputs[1].default_value = 0.9
    scale1_node.inputs[2].default_value = 0.9
    scale2_node.inputs[1].default_value = 1/scale1_node.inputs[1].default_value
    scale2_node.inputs[2].default_value = 1/scale1_node.inputs[2].default_value

    links = tree.links
    links.new(image_node.outputs[0], alpha_over_node.inputs[1])
    links.new(render_layers_node.outputs[0], hue_sat_node.inputs[0])
    links.new(hue_sat_node.outputs[0], exposure_node.inputs[0])
    links.new(exposure_node.outputs[0], blur1_node.inputs[0])
    links.new(blur1_node.outputs[0], scale1_node.inputs[0])
    links.new(scale1_node.outputs[0], pixelate_node.inputs[0])
    links.new(pixelate_node.outputs[0], scale2_node.inputs[0])
    links.new(scale2_node.outputs[0], blur2_node.inputs[0])
    links.new(blur2_node.outputs[0], alpha_over_node.inputs[2])
    links.new(alpha_over_node.outputs[0], composite_node.inputs[0])
    links.new(alpha_over_node.outputs[0], viewer_node.inputs[0])


def edit_compositor(background_filepath, background_filename):
    """
    Modify render layer node to change background image to
    the current camera position.
    """
    tree = bpy.context.scene.node_tree
    image_node = tree.nodes["Image"]
    bpy.data.images.load(background_filepath, check_existing=True)
    image_node.image = bpy.data.images[background_filename]


def render_backgrounds(camera_locations):
    """
    Render the background image with emission shader before
    adding the shadow catcher plane.
    """
    cam_obj = bpy.data.objects["Camera"]

    # Set the render engine to Cycles
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = RENDER_SAMPLES
    scene.render.resolution_x, scene.render.resolution_y = render_resolution

    for i in range(0, NUMBER_OF_CAMERAS):
        curr_index = i + NUMBER_OF_CAMERAS*iteration
        cam_obj.location = camera_locations[i]
         # Render background before adding shadows
        background_filename = str(curr_index) + ".png"
        background_filepath = os.path.join(
            DATASET_PATH, "backgrounds", background_filename)
        scene.render.filepath = background_filepath
        bpy.ops.render.render(write_still = True)


def get_co_in_camera_space(scene, obj, co):
    """
    Transforms coordinates in the world space to
    the camera space.
    """
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, obj, co)
    return co_2d


def render_images_with_annotations(
    data, camera_locations, all_car_boxes, all_tractor_boxes):
    """
    Renders the final image of the car with its shadow.
    Saves the annotations for each rendered image.
    """
    prepare_compositor()

    cam_obj = bpy.data.objects["Camera"]
    scene = bpy.context.scene

    global iteration

    for cam_index in range(0, NUMBER_OF_CAMERAS):

        curr_index = cam_index + NUMBER_OF_CAMERAS*iteration

        data["images"].append({
        "id": curr_index,
        "file_name": "images/" + str(curr_index) + ".png",
        "width": render_resolution[0],
        "height": render_resolution[1]
        })

        cam_obj.location = camera_locations[cam_index]
        image_filename = str(curr_index) + ".png"
        image_filepath = os.path.join(DATASET_PATH, "images", image_filename)
        scene.render.filepath = image_filepath
        background_filepath = os.path.join(
            DATASET_PATH, "backgrounds", image_filename)
        edit_compositor(background_filepath, image_filename)
        bpy.ops.render.render(write_still = True)

        annotate_vehicle_coco(
            data, all_car_boxes, scene, cam_obj, curr_index, "car")
        if ADD_TRACTORS:
            annotate_vehicle_coco(
                data, all_tractor_boxes, scene, cam_obj, curr_index, "tractor")

        # Clear the file if it already exists
        with open(os.path.join(
            DATASET_PATH, "labels", str(curr_index) + ".txt"),
            "w", encoding="utf-8"):
            pass

        annotate_vehicles_yolo(
            all_car_boxes, scene, cam_obj, curr_index, "car")
        if ADD_TRACTORS:
            annotate_vehicles_yolo(
                all_tractor_boxes, scene, cam_obj, curr_index, "tractor")

    iteration += 1


def annotate_vehicles_yolo(
    all_vehicle_boxes, scene, cam_obj, curr_index, vehicle_type):
    """
    Write yolo annotations of cars.
    """
    for box in all_vehicle_boxes:
        out_of_the_image = 0
        for point in box:
            point_co_in_camera = get_co_in_camera_space(scene, cam_obj, point)

            if((point_co_in_camera[0] > 1 or point_co_in_camera[0] < 0) or
                (point_co_in_camera[1] > 1 or point_co_in_camera[1] < 0)):
                out_of_the_image += 1
        # All four points must be out of the image to ignore the car
        if out_of_the_image == 4:
            print("Out of the image!\n")
        else:
            box_x_coordinates = []
            box_y_coordinates = []
            for point in box:
                point_co_in_camera = get_co_in_camera_space(
                    scene, cam_obj, point)

                if point_co_in_camera[0] > 1:
                    point_co_in_camera[0] = 1
                if point_co_in_camera[0] < 0:
                    point_co_in_camera[0] = 0
                if point_co_in_camera[1] > 1:
                    point_co_in_camera[1] = 1
                if point_co_in_camera[1] < 0:
                    point_co_in_camera[1] = 0

                box_x_coordinates.append(point_co_in_camera[0])
                box_y_coordinates.append(point_co_in_camera[1])

            bounding_box = return_yolo_box(box_x_coordinates, box_y_coordinates)

            category_id = ALL_VEHICLES.index(vehicle_type)

            with open(os.path.join(
                DATASET_PATH, "labels", str(curr_index) + ".txt"), "a",
                encoding="utf-8") as f:
                f.write(str(category_id) + " " +
                    str(bounding_box[0]) + " " + str(bounding_box[1]) + " " +
                    str(bounding_box[2]) + " " + str(bounding_box[3]) + "\n")


def annotate_vehicle_coco(
        data, all_vehicle_boxes, scene, cam_obj, cam_index, vehicle_type):
    """
    Write coco annotations of cars.
    """
    for box in all_vehicle_boxes:
        out_of_the_image = 0
        for point in box:
            point_co_in_camera = get_co_in_camera_space(scene, cam_obj, point)

            if((point_co_in_camera[0] > 1 or point_co_in_camera[0] < 0) or
                (point_co_in_camera[1] > 1 or point_co_in_camera[1] < 0)):
                out_of_the_image += 1
        # All four points must be out of the image to ignore the car
        if out_of_the_image == 4:
            print("Out of the image!\n")
        else:
            box_x_coordinates = []
            box_y_coordinates = []
            for point in box:
                point_co_in_camera = get_co_in_camera_space(
                    scene, cam_obj, point)

                if point_co_in_camera[0] > 1:
                    point_co_in_camera[0] = 1
                if point_co_in_camera[0] < 0:
                    point_co_in_camera[0] = 0
                if point_co_in_camera[1] > 1:
                    point_co_in_camera[1] = 1
                if point_co_in_camera[1] < 0:
                    point_co_in_camera[1] = 0

                box_x_coordinates.append(point_co_in_camera[0])
                box_y_coordinates.append(point_co_in_camera[1])

            bounding_box = return_coco_box(
                box_x_coordinates, box_y_coordinates, scene)
            category_id = ALL_VEHICLES.index(vehicle_type)
            data = create_coco(data, cam_index, category_id, bounding_box)


def main():
    """
    Main function that creates the dataset.
    """
    # Create yolo labels folder if it does not exist
    if not os.path.exists(os.path.join(DATASET_PATH, "labels")):
        os.makedirs(os.path.join(DATASET_PATH, "labels"))

    # Transform color space to standard to keep the map color same as original
    bpy.context.scene.view_settings.view_transform = "Standard"

    data = {
        "description": {"year":2023},
        "licenses": [],
        "categories": [
            {"id": 0, "name": "car"},
            {"id": 1, "name": "tractors"}],
        "images": [],
        "annotations": []
        }

    for _ in range(0, LANDS_COUNT):
        import_map_and_roads()

        max_x = bpy.data.objects["EXPORT_GOOGLE_SAT_WM"].dimensions.x / 2
        max_y = bpy.data.objects["EXPORT_GOOGLE_SAT_WM"].dimensions.y / 2

        car_count = 0
        while car_count < NUMBER_OF_CARS:
            cars_added = add_new_car(max_x, max_y)
            car_count += cars_added

        if ADD_TRACTORS:
            add_farm_vehicles(max_x, max_y)

        bpy.ops.object.camera_add(location=(0, 0, CAMERA_HEIGHT))
        bpy.data.scenes["Scene"].camera = bpy.data.objects["Camera"]

        camera_locations = decide_camera_locations(max_x, max_y)

        add_sun()
        render_backgrounds(camera_locations)
        add_shadow_catcher()

        all_car_boxes = get_all_cars_bounding_boxes()
        all_tractor_boxes = get_all_tractors_bounding_boxes()
        render_images_with_annotations(
            data, camera_locations, all_car_boxes, all_tractor_boxes)

    filename = os.path.join(DATASET_PATH, "label.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f)

    bpy.ops.wm.save_as_mainfile(filepath = MAIN_PATH + "test.blend")


if __name__ == "__main__":
    main()
