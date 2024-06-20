# synthetic_dataset_generation_system_for_vehicle_detection
![12](https://github.com/ProtostarLabs/synthetic_car_dataset_for_vehicle_detection/assets/155420688/49ef8465-96ba-41ef-8e04-7ec842ca0ed7)

**Overview**  
This project is a Python package that creates annotated synthetic images of vehicles on roads using 3D modeling. Images are taken from an aerial viewpoint. Annotations are bounding boxes in YOLO and COCO format. By replacing the models in the Vehicles folder, variety of vehicles on the images can be controlled and Lands files can also be replaced with custom ones.
Datasets created with this package can be used for vehicle detection model training.  

**Features**  
Modify vehicle models used to fit a special detection use case dataset.
Modify lands files to customize the scenery.
Export bounding box annotations in two most popular formats for machine learning: YOLO and COCO.
Control the resolution and altitude at which the images are taken.  

**Requirements**  
Blender software, tested with 3.6.5 version.  
Python 3.10 or higher and the following packages:  
Pandas  
Numpy  
Shapely  
GeoPandas  

**Installation**  
Clone this repository to your local machine.  
Install Blender software and all the required packages as Python modules in Blender.  
To do so, navigate to your Blender installation folder, go to version_folder/python/bin, in this case “3.6/python/bin” and run the following command for each package:  
./python3.10  -m pip install [package_name]

Download the Vehicles and Lands folders from the link below and place them into this repository folder.  
Link to assets https://drive.google.com/drive/folders/1Ovo127oIEZwT1bzzDcQTVDM0aE5Dfkhi?usp=sharing

**Running**  
Edit the config file of this project to fit your needs. Change the MAIN_PATH to the path to where you downloaded this repository and DATASET_PATH to where you want to create your dataset.  
In this project directory run the following command:  
[path_to_blender_executable] --background --python create_synthetic_dataset.py
