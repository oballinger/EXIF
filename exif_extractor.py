from PIL import Image
import streamlit.components.v1 as components
from pathlib import Path
import os
import shutil
import base64
from io import StringIO
import exifread
import folium
#import geopandas as gpd
#from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def makelist(extensions, source_dir):
    templist=[]
    for subdir, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in ['Faces','Clusters']]
        for file in files:
            for extension in extensions:
                if extension in os.path.join(subdir, file):
                    f=os.path.join(subdir, file)
                    templist.append(f)
    return templist

def overwrite(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)

def extract_metadata(source_dir):

    img_list=makelist(['.jpg', '.jpeg'], source_dir)
    metadata=pd.DataFrame()
    keys = ['EXIF DateTimeOriginal', 'Image Make', 'Image Model', 'EXIF BodySerialNumber',
    ]

    for image_path in img_list:
        f = open(image_path, 'rb')
        tags = exifread.process_file(f, details=False)
        exif_row = {key: str(tags[key]) for key in keys if key in tags.keys()}
        if len(exif_row)==0:
            exif_row=dict.fromkeys(keys,np.nan)
        metadata=metadata.append(exif_row, ignore_index=True)

        try:
            alt=process(tags.get('GPS GPSAltitude'))
            speed=process(tags.get('GPS GPSSpeed'))
            direction=process(tags.get('GPS GPSImgDirection'))
            getGPS(tags)    
        except:
            pass

    metadata['Filename']=img_list
    metadata['Filename']=metadata['Filename'].str.split('/').str[-1]
    metadata['EXIF DateTimeOriginal']=pd.to_datetime(metadata['EXIF DateTimeOriginal'],  format='%Y:%m:%d %H:%M:%S', errors='coerce')

    metadata.to_csv('metadata.csv')
    return metadata

def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)


def getGPS(tags):
    latitude = tags.get('GPS GPSLatitude')
    latitude_ref = tags.get('GPS GPSLatitudeRef')
    longitude = tags.get('GPS GPSLongitude')
    longitude_ref = tags.get('GPS GPSLongitudeRef')
    if latitude:
        lat_value = _convert_to_degress(latitude)
        if latitude_ref.values != 'N':
            lat_value = -lat_value
    else:
        return {}
    if longitude:
        lon_value = _convert_to_degress(longitude)
        if longitude_ref.values != 'E':
            lon_value = -lon_value
    else:
        return {}
    return {'latitude': lat_value, 'longitude': lon_value}


def process(value):
	return float(value.values[0].num) / float(value.values[0].den)


def add_marker(image_path, emap):

    keys = ['EXIF DateTimeOriginal', 'Image Make', 'Image Model', 'EXIF BodySerialNumber',
    'GPS GPSLatitudeRef',
    'GPS GPSLatitude',
    'GPS GPSLongitudeRef',
    'GPS GPSLongitude',
    'GPS GPSAltitudeRef',
    'GPS GPSAltitude',
    'GPS GPSSpeedRef',
    'GPS GPSSpeed',
    'GPS GPSImgDirectionRef',
    'GPS GPSImgDirection',
    'GPS GPSDestBearingRef',
    'GPS GPSDestBearing',
    'GPS GPSDate',
    'GPS Tag 0x001F',
    'Image GPSInfo'
    ]

    f = open(image_path, 'rb')
    tags = exifread.process_file(f, details=False)
    exif_row = {key: str(tags[key]) for key in keys if key in tags.keys()}
    if len(exif_row)==0:
        exif_row=dict.fromkeys(keys,np.nan)

    print(exif_row)
    alt=process(tags.get('GPS GPSAltitude'))
    speed=process(tags.get('GPS GPSSpeed'))
    direction=process(tags.get('GPS GPSImgDirection'))

    print('altitude:', alt)
    print('speed:', speed)
    print('direction:', direction)

    point=list(getGPS(tags).values())

    html = '<img src="{}" width=500px> <p>{}<p>'.format(image_path, text)
    iframe = folium.IFrame(html, width=400, height=300)
    popup = folium.Popup(iframe)

    marker= folium.RegularPolygonMarker(location=point, tooltip=html, popup = popup, fill_color='blue', number_of_sides=1, radius=20, rotation=bearing).add_to(emap)

extract_metadata('tmp/')
def plot_pics(df):
    emap = folium.Map(point)
    tile = folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = True,
            control = True
        ).add_to(emap)

    image_path='test/IMG_5506.jpg'

    emap.save("mymap.html")
