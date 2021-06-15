from flask import request
from flask_restful import Resource, abort
from sqlalchemy import func
from marshmallow import ValidationError
from zembil import db
from zembil.models import LocationModel
from zembil.schemas import LocationSchema

location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)

class Locations(Resource):
    def get(self):
        results = LocationModel.query.all()
        return locations_schema.dump(results)

    def post(self):
        data = request.get_json()
        try:
            args = location_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        existingLocation = LocationModel.query.filter_by(
            latitude=args['latitude'],
            longitude=args['longitude']
        )
        if existingLocation:
            abort(409, message="Shop with this location already exists")
        location = LocationModel(
            latitude=args['latitude'], 
            longitude=args['longitude'], 
            description=args['description']
        )
        db.session.add(location)
        db.session.commit()
        return location_schema.dump(location), 201

class Location(Resource):
    def get(self, id):
        result = LocationModel.query.filter_by(id=id).first()
        if not result:
            abort(404, message="Location Not Found")
        return location_schema.dump(result)


class LocationNearMe(Resource):
    def get(self):
        latitude = request.args.get('lat')
        longitude = request.args.get('long')
        radius = request.args.get('range')
        if not radius:
            radius = 10
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
            locations =  LocationModel.query.filter(
                func.acos(func.sin(func.radians(latitude)) \
                * func.sin(func.radians(LocationModel.latitude)) \
                + func.cos(func.radians(latitude)) \
                * func.cos(func.radians(LocationModel.latitude)) \
                * func.cos(func.radians(LocationModel.longitude) \
                - (func.radians(longitude)))) * 6371 <= radius)
            return locations_schema.dump(locations)
        abort(400, message="No shops found near your location")