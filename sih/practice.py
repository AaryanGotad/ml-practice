from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app) # using the flask app as an api
app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# defining a relation in the db
class VideoModel(db.Model):
    # all the fields i want in my model
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, nullable=False)
    likes = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Video(name = {name}, views = {views}, like = {likes})"

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

class Video(Resource):
    # we can add this above whichever method's output i want it to be serialised
    @marshal_with(resource_fields) # when we return, serialize it inn the given format
    def get(self, video_id):
        # abort_if_video_id_doesnt_exist(video_id)
        result = VideoModel.query.get(id=video_id)
        return result
    
    @marshal_with(resource_fields)
    def put(self, video_id):
        # abort_if_video_exists(video_id)
        args = video_put_args.parse_args()
        video = VideoModel(id=video_id, name=args['name'], views=args['views'], likes=args['likes'])
        db.session.add(video)
        db.session.commit()
        return video, 201 # 201 means 'created', by default the status code is '200' meaning 'ok'
    
    def delete(self, video_id):
        # abort_if_video_id_doesnt_exist(video_id)
        del videos[video_id]
        return 'Video deleted successfully!', 204

api.add_resource(HelloWorld, "/helloworld/<string:name>") # adding this class as a resource, which means this class will be called
                                                          #  when the mentioned URL (in this case the default URL) is called

api.add_resource(Video, "/video/<int:video_id>")

if __name__ == "__main__":
    app.run(debug=True) # this should only be done in a development enviroment, and not in a production enviroment