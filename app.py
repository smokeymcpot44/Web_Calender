from flask import Flask, abort
from flask_restful import Api, Resource, reqparse, inputs
from flask_restful import fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
import sys
import datetime

app = Flask(__name__)

# For RESTful api
api = Api(app)
# For working with db with SQLAlchemy
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myevents.sqlite'


# DB table using SQLAlchemy
class EventDb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)


# Creating tables
db.create_all()

# Format for decorator to send API data
resource_fields = {
    "id": fields.Integer,
    "event": fields.String,
    "date": fields.String,
}


# API request handler
# Returns today's events
class EventsTodayResource(Resource):
    # Decorator converting to JSON &
    # Formatting the return data according to resource_field
    @marshal_with(resource_fields)
    def get(self):
        db_data = EventDb.query.filter(EventDb.date == datetime.date.today()).all()
        return db_data


# API request handler
class EventResource(Resource):
    # Returns all the events or events b/w certain period
    @marshal_with(resource_fields)
    def get(self):
        # Parsing the incoming query parameters if specified
        my_parser = reqparse.RequestParser()
        my_parser.add_argument("start_time", type=inputs.date)
        my_parser.add_argument("end_time", type=inputs.date)
        get_args = my_parser.parse_args()
        if get_args['start_time']:
            events = EventDb.query.filter(
                EventDb.date.between(get_args['start_time'], get_args['end_time'])
            ).all()
            return events
        else:
            db_data = EventDb.query.all()
            return db_data

    # Adds event to DB
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("event",
                    type=str,
                    help="The event name is required!",
                    required=True)
        parser.add_argument("date",
                    type=inputs.date,
                    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                    required=True)
        args = parser.parse_args()
        new_event = EventDb(event=args['event'], date=args['date'])
        db.session.add(new_event)
        db.session.commit()
        send_data = {'message': "The event has been added!",
                     "event": args["event"],
                     "date": str(args['date'].date())}
        return send_data


class EventByID(Resource):
    @marshal_with(resource_fields)
    def get(self, event_id):
        event = EventDb.query.filter(EventDb.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = EventDb.query.filter(EventDb.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}


# Adding API request handler for requested URL
api.add_resource(EventResource, "/event")
api.add_resource(EventsTodayResource, "/event/today")
api.add_resource(EventByID, '/event/<int:event_id>')


# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
