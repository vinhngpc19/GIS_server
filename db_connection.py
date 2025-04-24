import pymongo

url = 'mongodb://localhost:27017'

client = pymongo.MongoClient(url)

db = client['gis_disaster_db']

polygon_collection = db['polygon']
user_collection = db['user']
flood_collection = db['flood']
erosion_collection = db['erosion']