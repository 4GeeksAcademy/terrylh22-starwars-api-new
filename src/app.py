"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets, People, user_favorite_planets, user_favorite_people
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_users():

    users = User.query.all()
    all_users = list(map(lambda x: x.serialize(), users))

    return jsonify(all_users), 200

@app.route('/user/<int:user_id>', methods=['GET'])
def get_specific_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user.serialize()), 200


@app.route('/user', methods=['POST'])
def add_user():

    requested = request.get_json()

    user1 = User(first_name=requested["first_name"], last_name=requested["last_name"], email=requested["email"], username=requested["username"], password=requested["password"])
    db.session.add(user1)
    db.session.commit()

    return jsonify(requested), 200

@app.route('/users/favorites', methods=['GET'])
def get_favorites():
    users = User.query.with_entities(User.favorite_planets, User.favorite_people).all()
    favorites = [{'favorite_planets': user.favorite_planets, 'favorite_people': user.favorite_people} for user in users]

    return jsonify(favorites), 200

@app.route('/favorite', methods=['POST'])
def add_favorite_planet():
    requested = request.get_json()
    favorite = {}
    if requested.get('planet_id'):
        favorite = user_favorite_planets(user_id=requested["planet_id"], planet_id=requested["planet_id"])
        db.session.add(favorite)
        db.session.commit()
        return jsonify("planet added to favorite"), 200
    elif requested.get('person_id'):
        favorite = user_favorite_planets(user_id=requested["user_id"], person_id=requested["person_id"])
        db.session.add(favorite)
        db.session.commit()
        return jsonify("person added to favorite"), 200
    else:
        return jsonify("no favorite found to add"), 200


@app.route('/planets', methods=['GET'])
def get_planets():

    planets = Planets.query.all()
    all_planets = list(map(lambda x: x.serialize(), planets))

    return jsonify(all_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_specific_planet(planet_id):
    planet = Planets.query.get(planet_id)
    if planet is None:
        return jsonify({'message': 'Planet not found'}), 404
    return jsonify(planet.serialize()), 200

@app.route('/people', methods=['GET'])
def get_people():

    people = People.query.all()
    all_people = list(map(lambda x: x.serialize(), people))

    return jsonify(all_people), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_specific_person(people_id):
    people = People.query.get(people_id)
    if people is None:
        return jsonify({'message': 'Person not found'}), 404
    return jsonify(people.serialize()), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
