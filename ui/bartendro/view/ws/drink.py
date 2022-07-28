# -*- coding: utf-8 -*-

# ---
import json
from time import sleep
from operator import itemgetter
from bartendro import app, db, mixer
from flask import Flask, request, Response
from flask.ext.login import login_required, current_user
from sqlalchemy.sql import text
from werkzeug.exceptions import ServiceUnavailable, BadRequest, InternalServerError
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName
from bartendro.model.booze import Booze
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.dispenser import Dispenser
from bartendro.error import BartendroBusyError, BartendroBrokenError, BartendroCantPourError, BartendroCurrentSenseError
import json


@app.route('/ws/drink/match/<str>')
def ws_drink_match(str):
    ''' Does a case insensitive search on drinks for the partial string.
    entering 'equ' will find all of the tequilla sunrises. '''
    str = "%%%s%%" % str
    drinks = db.session.query("id", "name").from_statement(text("SELECT id, name FROM drink_name  WHERE name LIKE :s")).params(s=str).all()
    js = json.dumps(drinks)
    resp=Response(js, status=200, mimetype="application/json")
    return resp



def ws_make_drink(drink_id):
    recipe = {}
    size=0
    drink = Drink.query.filter_by(id=int(drink_id)).first()
    for arg in request.args:
        if arg[0:4] == 'size':
            size = int(request.args.get(arg))
        else:
            booze = int(arg[5:])
            recipe[booze] = int(request.args.get(arg))

    # todo: add values for recipe_return array for drinks which use the
    # normal menu. OTOH, you won't see the response unless you are calling 
    # ws_make_drink from the API
    recipe_return = []
    if size:
        # figure out the recipe based on the drink
        size_unit = 150 / sum([db.value for db in drink.drink_boozes])
        # recipe is a dict of {booze_id:quantity, }
        recipe = {b.booze_id:b.value*size_unit for b in drink.drink_boozes}
        recipe_return = [ {'booze_id':b.booze_id, 'booze_name':b.booze.name, 'quantity':b.value*size_unit} for b in drink.drink_boozes]

    js = json.dumps({'drink_name':drink.name.name,'drink_description':drink.desc, 'boozes':recipe_return})

    try:
        app.mixer.make_drink(drink, recipe)
    except mixer.BartendroCantPourError as err:
        raise BadRequest(err)
    except mixer.BartendroBrokenError as err:
        raise InternalServerError(err)
    except mixer.BartendroBusyError as err:
        raise ServiceUnavailable(err)

    # todo: I'd like to return more than ok

    resp = Response(js, status=200, mimetype='application/json')
    return resp
    #return "%r\nok\n" % recipe

@app.route('/ws/drink/<int:drink>')
def ws_drink(drink):
    drink_mixer = app.mixer
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    return ws_make_drink(drink)

@app.route('/ws/drink/custom')
def ws_custom_drink():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    return ws_make_drink(0)

@app.route('/ws/drink/<int:drink>/available/<int:state>')
def ws_drink_available(drink, state):
    if not drink:
        db.session.query(Drink).update({'available' : state})
    else:
        db.session.query(Drink).filter(Drink.id==drink).update({'available' : state})
    db.session.flush()
    db.session.commit()
    return "ok\n"

@app.route('/ws/shots/<int:booze_id>')
def ws_shots(booze_id):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    dispensers = db.session.query(Dispenser).all()
    dispenser = None
    for d in dispensers:
        if d.booze.id == booze_id:
            dispenser = d

    if not dispenser:
        return "this booze is not available"

    try:
        app.mixer.dispense_shot(dispenser, app.options.shot_size)
    except mixer.BartendroCantPourError as err:
        raise BadRequest(err)
    except mixer.BartendroBrokenError as err:
        raise InternalServerError(err)
    except mixer.BartendroBusyError as err:
        raise ServiceUnavailable(err)

    return ""

@app.route('/ws/drink/<int:id>/load')
@login_required
def ws_drink_load(id):
    return drink_load(id)

def drink_load(id):
    drink = Drink.query.filter_by(id=int(id)).first()
    boozes = []
    for booze in drink.drink_boozes:
        boozes.append((booze.booze_id, booze.value))
    drink = { 
        'id'         : id,
        'name'       : drink.name.name,
        'desc'       : drink.desc,
        'popular'    : drink.popular,
        'available'  : drink.available,
        'boozes'     : boozes,
        'num_boozes' : len(boozes)
    }
    return json.dumps(drink)

@app.route('/ws/drink/<int:drink>/save', methods=["POST"])
def ws_drink_save(drink):

    data = request.json['drink']
    id = int(data["id"] or 0)
    if id > 0:
        drink = Drink.query.filter_by(id=int(id)).first()
        # If the drink name has changed copy to a new drink
        if drink.name != data['name'] :
            id = 0
            drink = Drink()
            for booze in data['boozes']:
                # clear the old_booze_id's 
                booze[2] = 0
            db.session.add(drink)
    else:
        id = 0
        drink = Drink()
        db.session.add(drink)

    try:
        drink.name.name = data['name']
        drink.desc = data['desc']
        if data['popular']:
            drink.popular = True
        else:
            drink.popular = False
            
        if data['available']:
            drink.available = True
        else:
            drink.available = False
    except ValueError:
        raise BadRequest

    for selected_booze_id, parts, old_booze_id in data['boozes']:
        try:
            selected_booze_id = int(selected_booze_id) # this is the id that comes from the most recent selection
            old_booze_id = int(old_booze_id)     # this id is the id that was previously used by this slot. Used for
                                                 # cleaning up or updateing existing entries
            parts = int(parts)                   
        except ValueError:
            raise BadRequest

        # if the parts are set to zero, remove this drink_booze from this drink
        if parts == 0:
            if old_booze_id != 0:
                for i, dbooze in enumerate(drink.drink_boozes):
                    if dbooze.booze_id == old_booze_id:
                        db.session.delete(drink.drink_boozes[i])
                        break
            continue

        # if there is an old_booze_id, then update the existing entry
        if old_booze_id > 0:
            for drink_booze in drink.drink_boozes:
                if old_booze_id == drink_booze.booze_id:
                    drink_booze.value = parts
                    if (selected_booze_id != drink_booze.booze_id):
                        drink_booze.booze = Booze.query.filter_by(id=selected_booze_id).first()
                    break
        else:
            # Create a new drink-booze entry
            booze = Booze.query.filter_by(id=selected_booze_id).first()
            DrinkBooze(drink, booze, parts, 0)

    db.session.commit()
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")

    return drink_load(drink.id) 
