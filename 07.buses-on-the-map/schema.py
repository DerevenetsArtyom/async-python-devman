from marshmallow import Schema, fields, validate


class WindowBoundsSchema(Schema):
    msgType = fields.String(
        required=True, validate=validate.OneOf(["newBounds"])
    )
    data = fields.Nested("WindowBoundsDataSchema", required=True)


class WindowBoundsDataSchema(Schema):
    south_lat = fields.Float(required=True)
    north_lat = fields.Float(required=True)
    west_lng = fields.Float(required=True)
    east_lng = fields.Float(required=True)


class BusSchema(Schema):
    busId = fields.String(required=True)
    route = fields.String(required=True)
    lat = fields.Float(required=True)
    lng = fields.Float(required=True)
