from rest_framework.response import Response
from rest_framework.decorators import api_view
import geopandas as gpd
import json
import os
from django.conf import settings
from .models import polygon_collection

@api_view(['GET'])
def getFlood(request):
    shapefile_path = os.path.join(settings.BASE_DIR, 'data', 'HueCity_SHP', 'Huecity_Flood2022.shp')
    try:
        gdf = gpd.read_file(shapefile_path)
        # Convert a datetime column
        for column in gdf.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns:
            gdf[column] = gdf[column].astype(str)

        data = gdf.to_json()
        geojson_data = json.loads(data)

        # features = geojson_data.get('features', [])
        # if features:
        #     polygon_collection.insert_many(features)
        return Response(geojson_data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def getPolygon(request):
    id = request.GET.get('id')
    # shapefile_path = os.path.join(settings.BASE_DIR, 'data', 'HueCity_SHP', 'gadm40_VNM_1.shp')
    try:
    #     gdf = gpd.read_file(shapefile_path)
    #     gdf.crs = "EPSG:4326"
    #     data = gdf.to_json()
    #     geojson_data = json.loads(data)
        
        # features = geojson_data.get('features', [])
        # if features:
        #     polygon_collection.insert_many(features)
        result = polygon_collection.find_one(
            {"id": id},
            {"properties.NAME_1": 1, "geometry.coordinates": 1, "_id": 0}  
        )

        return Response(result, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def getAllProvinces(request):
    
    try:
        cursor = polygon_collection.find({}, {"id": 1, "properties.NAME_1": 1})

        result = [
            {
                "id": str(doc["id"]),
                "name_1": doc["properties"]["NAME_1"]
            }
            for doc in cursor if "properties" in doc and "NAME_1" in doc["properties"]
        ]
        return Response({"data": result}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    


