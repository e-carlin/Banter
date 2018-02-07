from plaid import Client
from plaid.errors import APIError, ItemError
from flask import request, make_response, jsonify
from flask_restful import Resource, abort
from flask import current_app

from banter_api.extensions import db
from banter_api.models.institution import Institution
from banter_api.models.account import Account

def get_plaid_client():
    try:
        current_app.logger.debug("Creating Plaid Client")
        client = Client(client_id=current_app.config.get('PLAID_CLIENT_ID'),
                        secret=current_app.config.get('PLAID_SECRET_KEY'),
                        public_key=current_app.config.get('PLAID_PUBLIC_KEY'),
                        environment=current_app.config.get('PLAID_ENV'))
    except Exception as e:
        current_app.logger.error("Error creating plaid client {}".format(e))
        response_object = {
                'status': '500',
                'message': 'Error connecting to Plaid',
                'code' : '5001'
            }
        abort(500, message=response_object)
    return client

def get_public_token_from_request(request):
    if('public_token' in request):
        return request['public_token']
    else:
        current_app.logger.error("Hello {}".format(request))
        response_object = {
                'status' : '400',
                'message' : 'Request malformed. plublic_token not found in body.',
                'code' : '???' # TODO: do
            }
        abort(400, message=response_object)

def exchange_public_token(public_token):
    current_app.logger.debug("Exchanging plaid public token '{}' for an access token".format(public_token))
    client = get_plaid_client()
    try:
        exchange_response = client.Item.public_token.exchange(public_token)
        current_app.logger.debug("Received response from Plaid '{}'".format(exchange_response))
        current_app.logger.info("Succesfully exchanged Plaid public token for an access token and item id!")
        return exchange_response
    except Exception as e:
        current_app.logger.error("Error exchanging public token with Plaid. This probably means the public token was malformed. Exception: "+str(e)) 
        response_object = {
                'status' : '400',
                'message' : 'Error exchanging public token with Plaid. This probably means the public token was malformed',
                'code' : '4002'
            }
        abort(400, message=response_object)

def get_request_as_dict(request):
    try:
        request_as_dict = request.get_json()
        current_app.logger.debug("Request JSON is: '{}'".format(request_as_dict))
        return request_as_dict
    except Exception as e:
        current_app.logger.error("Error parsing request as json: {}".format(e))
        abort(400, message="The supplied body was not valid JSON")


def save_exchange_response_data(data):
    plaid_institution_id = data['institution']['institution_id']
    institution = Institution.query.filter_by(plaid_institution_id=plaid_institution_id).first()
    if not institution:
        current_app.logger.debug("Insitution '{}' doesn't already exist in db. Creating institution...".format(data['institution']))
        try:
            institution = Institution(
                plaid_institution_id=plaid_institution_id,
                name=data['institution']['name']
            )
            db.session.add(institution)
            db.session.commit()
            current_app.logger.debug("Saved institution '{}' to db".format(institution))
        except Exception as e:
            current_app.logger.error("Error creating institution '{}'".format(institution))
            response_object = {
                'status' : '500',
                'message' : 'There was an error saving the institution. Please try again.',
                'code' : '5002'
            }
            abort(500, message=response_object)

    else:
        current_app.logger.debug("Institution found '{}'".format(institution))

    accounts = data['accounts']
    current_app.logger.debug("Saving accounts '{}' to db.".format(accounts))

    for accountDetails in accounts:
        current_app.logger.debug("Trying to save account {}.".format(accountDetails))
        plaid_account_id = accountDetails['id']
        if not Account.query.filter_by(plaid_account_id=plaid_account_id).first(): # If an account with this id is *not* already found
            try:
                account = Account(
                    plaid_account_id = plaid_account_id,
                    name = accountDetails["name"]
                )
                db.session.add(account)
                db.session.commit()
                current_app.logger.info("Saved account {}".format(accountDetails))
            except Exception as e:
                current_app.logger.error("Error saving account {}. \n {}".format(accountDetails, e)) # TODO: Should this be str(e)
    

class PlaidResource(Resource):
    def post(self):
        current_app.logger.info("Exchanging Plaid public token for an access token and item id.")

        request_as_dict = get_request_as_dict(request)

        public_token = get_public_token_from_request(request_as_dict)

        exchange_response = exchange_public_token(public_token)

        current_app.logger.debug("The plaid link_session_id is '{}'".format(request_as_dict['link_session_id']))

        # save_exchange_response_data(exchange_response) # TODO

        response_object = {
            'status' : '200',
            'message' : 'Scucess exchanging public token.',
            'code' : '2002'
        }
        return response_object, 200

        