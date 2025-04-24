import os
import json
import geopandas as gpd
from django.conf import settings
import django
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygis_server.settings")
django.setup()

from db_connection import polygon_collection

def storeProvinces(shapefile_path):
    try:
        gdf = gpd.read_file(shapefile_path)
        gdf.crs = "EPSG:4326"
        data = gdf.to_json()
        geojson_data = json.loads(data)
        
        features = geojson_data.get('features', [])
        if features:
            polygon_collection.insert_many(features)

            polygon_collection.update_many(
                {},
                {"$set": {"properties.position": None}}
            )
        print("Shapefile loaded successfully")
    except Exception as e:
        print(f"Error: {str(e)}")

#  To run this file independently: python utils/parse_shp_utils.py

if __name__ == "__main__":
    shapefile_path = os.path.join(settings.BASE_DIR, 'data', 'HueCity_SHP', 'gadm40_VNM_1.shp')
    storeProvinces(shapefile_path)