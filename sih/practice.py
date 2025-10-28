from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
import logging

app = Flask(__name__)
api = Api(app)  # using the flask app as an api
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning
# Uncomment this while debugging to see actual SQL emitted
# app.config['SQLALCHEMY_ECHO'] = True

# basic logging setup
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# defining a relation in the db
class VideoModel(db.Model):
    # all the fields i want in my model
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, nullable=False)
    likes = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Video(name = {self.name}, views = {self.views}, likes = {self.likes})"

names = {"aaryan": {"age": 19, "gender": "male"},
         "sakshi": {"age": 46, "gender": "female"},
         "vaishnavee": {"age": 16, "gender": "female"}}

# db.create_all() # do this only for the first run of the script
                # as it will re-write the db if not deleted after it

# a class to be called when the given URL is entered
class HelloWorld(Resource):
    # a method when a GET request is called on the url
    def get(self, name):
        return names[name] # returns a dictionary containing 'Hello World', just to try out
    
    def post(self):
        return {"data": "Posted"}

# this is help us parse multiple arguments in the /videos url
video_put_args = reqparse.RequestParser()

# defining what arguments are acceptable
video_put_args.add_argument("name", type=str, help="Name of the video is required", required=True)
video_put_args.add_argument("likes", type=int, help="Likes on the video is required", required=True)
video_put_args.add_argument("views", type=int, help="Views on the video is required", required=True)

# argumets to update video details
video_update_args = reqparse.RequestParser()
video_update_args.add_argument("name", type=str, help="Name of the video is required")
video_update_args.add_argument("likes", type=int, help="Likes on the video is required")
video_update_args.add_argument("views", type=int, help="Views on the video is required")


# videos = {} # a dictionary storing video informaton having video_id as the key

# this method will send an appropriate status code and error message if the requested video does not exist
# def abort_if_video_id_doesnt_exist(video_id):
#     if video_id not in videos:
#         abort(404, message="Video id is not valid...")

# def abort_if_video_exists(video_id):
#     if video_id in videos:
#         abort(409, message="Video with the following video id already exists...")

# to define how an object is serialized
resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'views': fields.Integer,
    'likes': fields.Integer
}

def _get_video_by_id(video_id: int):
    """Helper to fetch a video by primary key, supporting both old and new Flask-SQLAlchemy patterns."""
    # Newer style (Flask-SQLAlchemy 3 / SQLAlchemy 2): use session.get
    try:
        if hasattr(db.session, 'get'):
            return db.session.get(VideoModel, video_id)
    except Exception:  # fall back to legacy
        pass
    # Legacy style (pre 3.x) if Model.query still exists
    if hasattr(VideoModel, 'query'):
        return VideoModel.query.get(video_id)
    # Fallback raw select
    stmt = db.select(VideoModel).where(VideoModel.id == video_id)
    return db.session.execute(stmt).scalar_one_or_none()


class Video(Resource):
    @marshal_with(resource_fields)
    def get(self, video_id):
        video = _get_video_by_id(video_id)
        if not video:
            abort(404, message="Video doesn't exist")
        return video

    @marshal_with(resource_fields)
    def put(self, video_id):
        args = video_put_args.parse_args()
        try:
            if _get_video_by_id(video_id):
                abort(409, message="Video already exists")
            video = VideoModel(id=video_id, name=args['name'], views=args['views'], likes=args['likes'])
            db.session.add(video)
            db.session.commit()
            logger.info(f"Created video id={video_id}")
            return video, 201
        except HTTPException:
            # Re-raise abort() exceptions so they aren't turned into 500s
            raise
        except IntegrityError as ie:
            db.session.rollback()
            logger.exception("Integrity error while creating video")
            abort(400, message=f"Integrity error: {ie.orig}")
        except Exception:
            db.session.rollback()
            logger.exception("Unexpected error in PUT /video/%s", video_id)
            abort(500, message="Internal server error")

    def delete(self, video_id):
        video = _get_video_by_id(video_id)
        if not video:
            abort(404, message="Video doesn't exist")
        try:
            db.session.delete(video)
            db.session.commit()
            logger.info(f"Deleted video id={video_id}")
            return '', 204
        except HTTPException:
            raise
        except Exception:
            db.session.rollback()
            logger.exception("Failed to delete video id=%s", video_id)
            abort(500, message="Internal server error")

    @marshal_with(resource_fields)
    def patch(self, video_id):
        args = video_update_args.parse_args()
        video = _get_video_by_id(video_id)
        if not video:
            abort(404, message="Video doesn't exist")

        updated = False
        if args.get('name') is not None:
            video.name = args['name']
            updated = True
        if args.get('views') is not None:
            video.views = args['views']
            updated = True
        if args.get('likes') is not None:
            video.likes = args['likes']
            updated = True

        if not updated:
            abort(400, message="No valid fields supplied for update")

        try:
            db.session.commit()
            logger.info(f"Patched video id={video_id}")
            return video, 200
        except HTTPException:
            raise
        except IntegrityError as ie:
            db.session.rollback()
            logger.exception("Integrity error while patching video id=%s", video_id)
            abort(400, message=f"Integrity error: {ie.orig}")
        except Exception:
            db.session.rollback()
            logger.exception("Unexpected error while patching video id=%s", video_id)
            abort(500, message="Internal server error")

class VideoList(Resource):
    """Debug/list endpoint to inspect all videos (not for production)."""
    def get(self):
        try:
            # Prefer new 2.0 style select
            stmt = db.select(VideoModel)
            rows = db.session.execute(stmt).scalars().all()
        except Exception:
            # Fallback legacy
            rows = VideoModel.query.all() if hasattr(VideoModel, 'query') else []
        return [
            {"id": v.id, "name": v.name, "views": v.views, "likes": v.likes}
            for v in rows
        ], 200


api.add_resource(HelloWorld, "/helloworld/<string:name>") # adding this class as a resource, which means this class will be called
                                                          #  when the mentioned URL (in this case the default URL) is called

api.add_resource(Video, "/video/<int:video_id>")
api.add_resource(VideoList, "/videos")  # debug listing endpoint

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True) # this should only be done in a development enviroment, and not in a production enviroment