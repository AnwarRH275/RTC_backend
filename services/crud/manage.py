
from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required
from models.model import Recipie
from models.exts import db

recipie_ns = Namespace('product', description='namespaces recipie ')

# model (serializer)
recipie_model = recipie_ns.model(
    "Recipie",
    {
        "id": fields.Integer(),
        "title": fields.String(),
        "description": fields.String()
    }
)


@recipie_ns.route("/recipies")
class RecipieRessource(Resource):

    @recipie_ns.marshal_list_with(recipie_model)
    @jwt_required()
    def get(self):
        '''Get all Recipies'''
        recipies = Recipie.query.all()
        return recipies

    @recipie_ns.marshal_with(recipie_model)
    @recipie_ns.expect(recipie_model)
    @jwt_required()
    def post(self):
        '''Create new recipie'''
        data = request.get_json()
        new_recipie = Recipie(
            title=data.get('title'),
            description=data.get('description')
        )
        new_recipie.save()
        return new_recipie, 201


@recipie_ns.route("/recipie/<int:id>")
class RecipieRessource(Resource):

    @recipie_ns.marshal_with(recipie_model)
    @jwt_required()
    def get(self, id):
        '''Get by id Recipie'''
        recipie = Recipie.query.get_or_404(id)

        return recipie

    @recipie_ns.marshal_with(recipie_model)
    @jwt_required()
    def put(self, id):
        '''update recipie'''
        recipie_to_update = Recipie.query.get_or_404(id)
        data = request.get_json()

        recipie_to_update.update(
            title=data.get('title'),
            description=data.get('description')
        )

        return recipie_to_update

    @recipie_ns.marshal_with(recipie_model)
    @jwt_required()
    def delete(self, id):
        '''delete recipie'''
        recipie_to_delete = Recipie.query.get_or_404(id)
        recipie_to_delete.delete()
        return recipie_to_delete

    @recipie_ns.route('/Hello')
    class HelloRessource(Resource):
        def get(self):
            return {"message": "hello word!!"}
