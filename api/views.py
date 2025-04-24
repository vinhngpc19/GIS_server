from rest_framework.response import Response
from rest_framework.decorators import api_view
import geopandas as gpd
import json
import os
from django.conf import settings
from db_connection import polygon_collection, user_collection, flood_collection, erosion_collection

@api_view(['GET'])
def get_flood(request):
    province = request.GET.get('province')
    try:
        flood_data = flood_collection.find_one({"province": province}, {'_id': 0})
        if not flood_data:
            return Response({"error": "Không tìm thấy dữ liệu lũ lụt"}, status=404)
            
        return Response(flood_data, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_erosion():
    shapefile_path = os.path.join(settings.BASE_DIR, 'data', 'HueCity_SHP', 'Diem_TL_ALuoi.shp')
    try:
        gdf = gpd.read_file(shapefile_path)
        # Convert a datetime column
        for column in gdf.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns:
            gdf[column] = gdf[column].astype(str)

        data = gdf.to_json()
        geojson_data = json.loads(data)

        return Response(geojson_data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def get_polygon(request):
    name = request.GET.get('name')
    if name == "Bà Rịa-Vũng Tàu":
        name = "Bà Rịa - Vũng Tàu"
    try:
        result = polygon_collection.find_one(
            {"properties.NAME_1": name},
            {"properties.NAME_1": 1, "geometry.coordinates": 1, "geometry.type": 1, "_id": 0}  
        )

        return Response({"data" :result}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_all_provinces(request):
    try:
        cursor = polygon_collection.find({}, {"id": 1, "properties.NAME_1": 1, "properties.position": 1})

        result = [
            {
                "id": str(doc["id"]),
                "name_1": doc["properties"]["NAME_1"],
                "position": doc["properties"]["position"],
            }
            for doc in cursor if "properties" in doc and "NAME_1" in doc["properties"]
        ]
        return Response({"data":{ "data": result}}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def update_position_province(request):
    try:
        name = request.data.get('name')
        position = request.data.get('position')

        if not name or position is None:
            return Response({"error": "Missing name or position"}, status=400)

        record = polygon_collection.find_one({"properties.NAME_1": name})

        if not record:
            return Response({"error": "Record not found"}, status=404)

        current_position = record.get("properties", {}).get("position")
        if current_position is not None:
            return Response({"error": "Position already has data"}, status=400)

        result = polygon_collection.update_one(
            {"properties.NAME_1": name},
            {"$set": {"properties.position": position}}
        )

        return Response({"message": "Position updated successfully"}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
def insert_user(request):
    try:
        email = request.data.get("email")
        username = request.data.get("username")

        if not email or not username:
            return Response({"error": "Missing email or username"}, status=400)

        # Kiểm tra xem email đã tồn tại chưa
        existing_user = user_collection.find_one({"email": email})
        if existing_user:
            return Response({"error": "Email already exists"}, status=400)

        # Chèn dữ liệu vào MongoDB
        new_user = {
            "email": email,
            "username": username
        }
        user_collection.insert_one(new_user)

        return Response({"message": "User inserted successfully"}, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
def add_disaster_data(request):
    try:
        # Lấy dữ liệu từ request (hỗ trợ cả form-urlencoded và JSON)
        if request.content_type.startswith('application/json'):
            data = request.data
        else:
            data = request.POST
        province = data.get('province')
        creation_date = data.get('CreationDa')
        place_name = data.get('Place_name')
        flood_house = data.get('FloodHouse')
        flood_road = data.get('FloodRoad')
        survey_date = data.get('SurveyDate')
        surveyer = data.get('Surveyer')
        lat = data.get('lat')
        lng = data.get('lng')
        image = data.get('image')
        is_flood = data.get('is_flood')
        # Kiểm tra kích thước ảnh nếu có
        if image:
            # Giả sử image là base64 string
            import base64
            try:
                # Kiểm tra kích thước base64 string (1MB = 1,048,576 bytes)
                image_size = len(base64.b64decode(image)) * 0.75  # base64 overhead
                if image_size > 5 * 1024 * 1024:  # Giới hạn 5MB
                    return Response({"error": "Kích thước ảnh không được vượt quá 5MB"}, status=400)
            except:
                return Response({"error": "Dữ liệu ảnh không hợp lệ"}, status=400)

        # Kiểm tra province có được gửi lên không
        if not province:
            return Response({"error": "Thiếu thông tin province"}, status=400)

        # Kiểm tra và chuyển đổi is_flood thành boolean
        is_flood = str(is_flood).lower() == 'true'
        
        # Chọn collection dựa trên is_flood
        collection = flood_collection if is_flood else erosion_collection
        
        # Lấy document của tỉnh
        province_doc = collection.find_one({"province": province})
        
        # Đếm số lượng features hiện có
        feature_count = len(province_doc.get("features", [])) if province_doc else 0
        
        # Tạo feature mới
        new_feature = {
            "type": "Feature",
            "id": str(feature_count),  # Thêm trường id mới dựa trên số lượng features
            "properties": {
                "CreationDa": creation_date,
                "Place_name": place_name,
                "FloodHouse": float(flood_house) if flood_house else 0,
                "FloodRoad": float(flood_road) if flood_road else 0,
                "SurveyDate": survey_date,
                "Surveyer": surveyer,
                "image": image
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(lng), float(lat)]
            },
            "is_user_send": True
        }

        # Kiểm tra và tạo mới document nếu chưa tồn tại
        collection.update_one(
            {"province": province},
            {
                "$setOnInsert": {
                    "type": "FeatureCollection",
                    "province": province,
                    "features": []
                }
            },
            upsert=True
        )

        # Thêm feature mới vào mảng features
        result = collection.update_one(
            {"province": province},
            {"$push": {"features": new_feature}}
        )

        return Response({
            "message": f"Thêm dữ liệu {'lũ lụt' if is_flood else 'sạt lở'} thành công cho tỉnh {province}"
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
def update_disaster_data(request):
    try:
        # Lấy dữ liệu từ request
        if request.content_type.startswith('application/json'):
            data = request.data
        else:
            data = request.POST
            
        province = data.get('province')
        feature_id = data.get('id')
        creation_date = data.get('CreationDa')
        place_name = data.get('Place_name')
        flood_house = data.get('FloodHouse')
        flood_road = data.get('FloodRoad')
        survey_date = data.get('SurveyDate')
        surveyer = data.get('Surveyer')
        lat = data.get('lat')
        lng = data.get('lng')
        image = data.get('image')
        is_flood = data.get('is_flood')

        print(f"Debug - Province: {province}")
        print(f"Debug - Feature ID: {feature_id}")
        print(f"Debug - Is Flood: {is_flood}")

        # Kiểm tra các trường bắt buộc
        if not province or not feature_id:
            return Response({"error": "Thiếu thông tin province hoặc id"}, status=400)

        # Kiểm tra và chuyển đổi is_flood thành boolean
        is_flood = str(is_flood).lower() == 'true'
        
        # Chọn collection dựa trên is_flood
        collection = flood_collection if is_flood else erosion_collection

        # Kiểm tra xem feature có tồn tại không
        province_doc = collection.find_one({
            "province": province,
            "features.id": feature_id
        })

        print(f"Debug - Province Doc: {province_doc}")

        if not province_doc:
            return Response({"error": "Không tìm thấy dữ liệu để cập nhật"}, status=404)

        # Lấy feature hiện tại
        current_feature = next((f for f in province_doc['features'] if f['id'] == feature_id), None)
        if not current_feature:
            return Response({"error": "Không tìm thấy feature"}, status=404)

        # Tạo object cập nhật
        update_data = {}
        if creation_date is not None and creation_date != current_feature['properties'].get('CreationDa'):
            update_data["properties.CreationDa"] = creation_date
        if place_name is not None and place_name != current_feature['properties'].get('Place_name'):
            update_data["properties.Place_name"] = place_name
        if flood_house is not None and float(flood_house) != current_feature['properties'].get('FloodHouse', 0):
            update_data["properties.FloodHouse"] = float(flood_house)
        if flood_road is not None and float(flood_road) != current_feature['properties'].get('FloodRoad', 0):
            update_data["properties.FloodRoad"] = float(flood_road)
        if survey_date is not None and survey_date != current_feature['properties'].get('SurveyDate'):
            update_data["properties.SurveyDate"] = survey_date
        if surveyer is not None and surveyer != current_feature['properties'].get('Surveyer'):
            update_data["properties.Surveyer"] = surveyer
        if image is not None and image != current_feature['properties'].get('image'):
            update_data["properties.image"] = image
        if lat is not None and lng is not None:
            current_coords = current_feature['geometry']['coordinates']
            if [float(lng), float(lat)] != current_coords:
                update_data["geometry.coordinates"] = [float(lng), float(lat)]

        print(f"Debug - Update Data: {update_data}")

        if not update_data:
            return Response({"message": "Không có thay đổi nào cần cập nhật"}, status=200)

        # Tạo query cập nhật
        update_query = {}
        for key, value in update_data.items():
            update_query[f"features.$.{key}"] = value

        print(f"Debug - Update Query: {update_query}")

        # Cập nhật feature
        result = collection.update_one(
            {
                "province": province,
                "features.id": feature_id
            },
            {"$set": update_query}
        )

        print(f"Debug - Modified Count: {result.modified_count}")
        print(f"Debug - Matched Count: {result.matched_count}")

        if result.modified_count == 0:
            return Response({"error": "Không thể cập nhật dữ liệu"}, status=400)

        return Response({
            "message": f"Cập nhật dữ liệu {'lũ lụt' if is_flood else 'sạt lở'} thành công cho tỉnh {province}"
        }, status=200)

    except Exception as e:
        print(f"Debug - Error: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def delete_disaster_data(request):
    try:
        # Lấy dữ liệu từ request
        if request.content_type.startswith('application/json'):
            data = request.data
        else:
            data = request.POST
            
        province = data.get('province')
        feature_id = data.get('id')
        is_flood = data.get('is_flood')

        # Kiểm tra các trường bắt buộc
        if not province or not feature_id:
            return Response({"error": "Thiếu thông tin province hoặc id"}, status=400)

        # Kiểm tra và chuyển đổi is_flood thành boolean
        is_flood = str(is_flood).lower() == 'true'
        
        # Chọn collection dựa trên is_flood
        collection = flood_collection if is_flood else erosion_collection

        # Xóa feature
        result = collection.update_one(
            {"province": province},
            {"$pull": {"features": {"id": feature_id}}}
        )

        if result.modified_count == 0:
            return Response({"error": "Không tìm thấy dữ liệu để xóa"}, status=404)

        return Response({
            "message": f"Xóa dữ liệu {'lũ lụt' if is_flood else 'sạt lở'} thành công cho tỉnh {province}"
        }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    