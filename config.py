import argparse
import os
import sys


if '--' in sys.argv:
    argv = sys.argv[sys.argv.index('--') + 1:]
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--cars_count', dest='cars_count', type=int, required=True)
parser.add_argument('-i', '--cameras_count', dest='cameras_count', type=int, required=True)
parser.add_argument('-l', '--lands_count', dest='lands_count', type=int, required=True)
args = parser.parse_known_args(argv)[0]

MAIN_PATH = "/home/pc4/Projekti/SyntheticCarDataset"
DATASET_PATH = "/home/pc4/Projekti/SyntheticCarDataset/dataset"

NUMBER_OF_CARS = args.cars_count #30
NUMBER_OF_FARM_VEHICLES = 30
RENDER_SAMPLES = 64
render_resolution = [640, 640]
# Final number of annotated images will be
# NUMBER_OF_CAMERAS * LANDS_COUNT
NUMBER_OF_CAMERAS = args.cameras_count #2
LANDS_COUNT = args.lands_count #2
CAMERA_HEIGHT = 221

ADD_TRACTORS = False

ALL_VEHICLES = ["car", "tractor"]

CAR_MODELS_COUNT = len([f for f in os.listdir(os.path.join(MAIN_PATH, "Vehicles", "Cars"))
     if f.endswith(".fbx") and
     os.path.isfile(os.path.join(MAIN_PATH, "Vehicles", "Cars", f))])

TRACTOR_MODELS_COUNT = len([f for f in os.listdir(os.path.join(MAIN_PATH, "Vehicles", "Tractors"))
     if f.endswith(".fbx") and
     os.path.isfile(os.path.join(MAIN_PATH, "Vehicles", "Tractors", f))])

LANDS_MODELS_COUNT = len([f for f in os.listdir(os.path.join(MAIN_PATH, "Lands"))
     if f.endswith(".blend") and
     os.path.isfile(os.path.join(MAIN_PATH, "Lands", f))])

car_colors = [
    (1.00, 1.00, 1.00, 1.00),   # white
    (0.08, 0.08, 0.08, 1.00),   # black
    (0.35, 0.35, 0.35, 1.00),   # grey
    (0.45, 0.45, 0.45, 1.00),   # silver
    (0.003, 0.216, 0.784 ,1),   # blue
    (0.686, 0.029, 0.029, 1),   # red
    (0.00, 0.50, 0.00, 1.00),   # green
    (0.119, 0.038, 0.0, 1.0),   # brown
    (1.00, 0.184, 0.00, 1.0),   # orange
    (1.00, 0.35, 0.100, 1.0),   # beige
    (0.528, 0.053, 0.370, 1),   # purple
    (0.723, 0.385, 0.045, 1),   # gold
    (1.000, 0.601, 0.008, 1)    # yellow
]

car_colors_weights = [
    0.233, 0.236, 0.152, 0.151, 0.085, 0.106, 0.008,
    0.017, 0.003, 0.003, 0.001, 0.003, 0.002
]
