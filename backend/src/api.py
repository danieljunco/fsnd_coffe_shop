from operator import methodcaller
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

## ROUTES

@app.route('/drinks', methods=['GET'])
def order_drinks():
    try:
        accessible_drinks = Drink.query.all()
        print(accessible_drinks)
        drinks = [drink.short() for drink in accessible_drinks]
        
        if drinks is None:
            abort(404)

        return jsonify({
            'success': True,
            'drinks': drinks,
            }), 200

    except Exception as e:
        print(e)
        abort(404)

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_detail(jwt):
    try:
        accessible_drinks = Drink.query.all()
        drinks = [drink.long() for drink in accessible_drinks]

        if drinks is None:
            abort(404)
        
        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200

    except Exception as e:
        print(e)
        abort(404)

@app.route('/drinks', methods= ['POST'])
@requires_auth('post:drinks')
def create_drink(jwt): 
    body = dict(request.form or request.json or request.data)
    drink = Drink(title=body.get('title'),
                  recipe=body.get('recipe') if type(body.get('recipe')) == str
                  else json.dumps(body.get('recipe')))
    try:
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except:
        return jsonify({
            'success': False,
            'error': "An error occurred"
        }), 500

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(jwt, drink_id):
    try:
        body = dict(request.form or request.json or request.data)
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink:
            drink.title = body.get('title') if body.get(
                'title') else drink.title
            recipe = body.get('recipe') if body.get('recipe') else drink.recipe
            drink.recipe = recipe if type(recipe) == str else json.dumps(
                recipe)
            drink.update()
            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            }), 200
        else:
            abort(404)
    except:
        return jsonify({
            'success': False,
            'error': "An error occurred"
        }), 500

@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def remove_drink(jwt,drink_id):
    try: 
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        drink.delete()
        return jsonify({
            'success': True,
            'delete': drink_id
        }), 200
    except:
        abort(404)


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400
    
@app.errorhandler(AuthError)
def authorization_error(error):
    return jsonify({
        "success": False, 
        "error": error.status_code,
        "message": error.error['code']
    }), error.status_code