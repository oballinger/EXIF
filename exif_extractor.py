from PIL import Image
import streamlit.components.v1 as components
from pathlib import Path
import os
import shutil
import base64
from io import StringIO
import exifread
import folium
from folium.plugins import MarkerCluster
#import geopandas as gpd
#from shapely.geometry import Polygon
import pandas as pd
import numpy as np
import math
import itertools

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
    md=pd.DataFrame()
    keys = ['EXIF DateTimeOriginal', 'Image Make', 'Image Model', 'EXIF BodySerialNumber','GPS GPSAltitude', 'GPS GPSSpeed', 'GPS GPSImgDirection'
    ]

    for image_path in img_list:
        f = open(image_path, 'rb')
        tags = exifread.process_file(f, details=False)
        exif_row = {key: str(tags[key]) for key in keys if key in tags.keys()}
        if len(exif_row)==0:
            exif_row=dict.fromkeys(keys,np.nan)
        exif_row=pd.DataFrame(exif_row, index=[0])

        try:
            coords=getGPS(tags)
            exif_row['Latitude'], exif_row['Longitude']=coords['latitude'], coords['longitude']
        except:
            exif_row['Latitude'],exif_row['Longitude']=np.nan, np.nan
        md=pd.concat([md, exif_row], ignore_index=True)

    md['Filename']=img_list
    md['Filename']=md['Filename'].str.split('/').str[-1]
    md['EXIF DateTimeOriginal']=pd.to_datetime(md['EXIF DateTimeOriginal'],  format='%Y:%m:%d %H:%M:%S', errors='coerce')
    df=pd.DataFrame()

    df['Filename'], df['Camera Make'], df['Camera Model'], df['Serial Number']=md['Filename'], md['Image Make'], md['Image Model'], md['EXIF BodySerialNumber']
    df['Date']=md['EXIF DateTimeOriginal'].dt.date
    df['Time']=md['EXIF DateTimeOriginal'].dt.time
    df['Direction']=md['GPS GPSImgDirection'].str.split('/').apply(lambda x: ratio(x))
    df['Altitude']=md['GPS GPSAltitude'].str.split('/').apply(lambda x: ratio(x))
    df['Speed']=md['GPS GPSSpeed'].str.split('/').apply(lambda x: ratio(x))
    df['Latitude'],df['Longitude']=md['Latitude'],md['Longitude']
    df.to_csv('metadata.csv')
    return df

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
    return {'latitude': round(lat_value, 4), 'longitude': round(lon_value,4)}


def ratio(x):
    try:
        return round(float(x[0])/float(x[1]), 2)
    except:
        return np.nan


def add_marker(row, emap):

    #row=row.astype(str)
    image_path='images/'+row['Filename']
    print(image_path)
    text=[]

    for i, v in zip(row.index, row.values):
        text.append('<strong>'+i+':</strong> '+str(v)+'<br>')

    text=str(text).replace(',', '').replace('\'','').replace('[','').replace(']','')
    point=list(row[['Latitude','Longitude']].values)
    bearing=row['Direction']
    
    html = '<img src="{}" width=500px> <p>{}<p>'.format(image_path, text)
    iframe = folium.IFrame(html, width=400, height=300)
    popup = folium.Popup(iframe)

    try:
        if bearing==bearing:
            marker= folium.RegularPolygonMarker(location=point, tooltip=html, popup = popup, color='red', number_of_sides=3, radius=20, rotation=bearing).add_to(emap)
        else:
            marker= folium.Marker(location=point, tooltip=html, popup = popup, color='red').add_to(emap)
    except:
        pass


def plot_pics(tempdir):
    df= extract_metadata(tempdir)

    emap = folium.Map()
    #marker_cluster = folium.plugins.MarkerCluster().add_to(emap)

    
    tile = folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = True,
            control = True
        ).add_to(emap)

    for _,i in df.iterrows():
        add_marker(i, emap)

    sw = df[['Latitude', 'Longitude']].min().values.tolist()
    ne = df[['Latitude', 'Longitude']].max().values.tolist()
    emap.fit_bounds([sw, ne]) 

    emap.save("mymap.html")

    return emap
