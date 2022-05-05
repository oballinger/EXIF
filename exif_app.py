import streamlit as st
import exif_extractor as ex
from PIL import Image
import streamlit.components.v1 as components
from pathlib import Path
import os
import shutil
import base64
import PIL 
import pillow_heif
from io import StringIO

st.set_page_config(
        page_title="Exif Extractor"    )


tempdir=Path('tmp/')

st.title('Image Metadata Extractor')

st.write('This tool extracts metadata from images.')

st.header('Step 1: Upload Images')

uploaded_files = st.file_uploader("Please ensure the images are either .jpg/.jpeg/.HEIC files. If you have lots of images, compressing the files can help speed things up.",accept_multiple_files=True, type=['jpeg','jpg','HEIC'])

@st.cache
def Ingest():
	ex.overwrite(tempdir)
	for uploaded_file in uploaded_files:
		try:
			if uploaded_file.type=="image/heic":
				heif_file = pillow_heif.read_heif(uploaded_file)
				img = Image.frombytes(
				    heif_file.mode,
				    heif_file.size,
				    heif_file.data,
				    "raw")
				tags=heif_file.info['exif']
			else:
				img = Image.open(uploaded_file)
				tags= img.getexif()

			filename=uploaded_file.name.split('.')[0]+'.jpg'
			img.save(os.path.join(tempdir,filename), format='JPEG', optimize=True, quality=10, exif=tags)
		except:
			pass
if len(uploaded_files)>0:
	Ingest()

with st.sidebar:
	option=st.selectbox('Test Datasets:', 
		('Select...','Kurdish Rebels','The Godfather','Parler')
		)
	if option=='Kurdish Rebels':
		tempdir='PKK/'
		st.write('This dataset contains a sample of 50 images scraped from the obituary website of a Kurdish rebel group known as the PKK. [Click here](https://oballinger.github.io/PICAN-data) to view the full dataset. Present in these photographs is Murat Karayilan (the leader of the PKK), Ekrem Güney (a top lieutenant), and several foot soldiers.')
		st.write('Click the "Cluster" button to identify these individuals across the images. The largest cluster is Ekrem Güney. The next two are foot soldiers, and the fourth largest cluster is PKK leader Murat Karayilan.')
		st.write('Finally, click the "Generate Network" button to identify these individuals across the images. Though Karayilan (Node #4) does not appear in that many pictures, everyone in these photographs has posed with him. He also poses most frequently with his Lieutenant, Ekrem Güney (Node #1).')
    

st.header('Step 2: Analyze')

meta_button = st.button("Extract Metadata")
if meta_button:
	meta=ex.extract_metadata(tempdir)
	st.write(meta)

geo_button = st.button("Map Photographs")
if geo_button:
	static_dir = Path(st.__path__[0]) / 'static/images'

	if static_dir.exists():
		shutil.rmtree(static_dir)

	shutil.copytree(str(tempdir), static_dir)
	geo=ex.plot_pics(tempdir)
	
	HtmlFile = open("mymap.html", 'rb')
	source_code = HtmlFile.read()		
	components.html(source_code, height=720, width=720)


