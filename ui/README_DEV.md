# Developer notes on hello drinkbot fork of bartendro

#  July 2022

## A list of all of the routes

In bartender/

grep -r 'app.route' ui/*


ui/README_DEV.md:grep -r 'app.route' ui/*
ui/bartendro/view/booze.py:@app.route('/booze')
ui/bartendro/view/booze.py:@app.route('/booze/<int:id>')
ui/bartendro/view/booze.py:@app.route('/booze/all')
ui/bartendro/view/booze.py:@app.route('/booze/loaded')
ui/bartendro/view/trending.py:@app.route('/trending')
ui/bartendro/view/trending.py:@app.route('/trending/date/')
ui/bartendro/view/trending.py:@app.route('/trending/<int:hours>')
ui/bartendro/view/snooze.py:@app.route('/snooze')
ui/bartendro/view/admin/options.py:@app.route('/admin/options')
ui/bartendro/view/admin/options.py:@app.route('/admin/lost-passwd')
ui/bartendro/view/admin/options.py:@app.route('/admin/upload')
ui/bartendro/view/admin/dispenser.py:@app.route('/admin')
ui/bartendro/view/admin/dispenser.py:@app.route('/admin/save', methods=['POST'])
ui/bartendro/view/admin/user.py:@app.route("/admin/login", methods=["GET", "POST"])
ui/bartendro/view/admin/user.py:@app.route("/admin/logout")
ui/bartendro/view/admin/booze.py:@app.route('/admin/booze')
ui/bartendro/view/admin/booze.py:@app.route('/admin/booze/edit/<id>')
ui/bartendro/view/admin/booze.py:@app.route('/admin/booze/save', methods=['POST'])
ui/bartendro/view/admin/drink.py:@app.route('/admin/drink')
ui/bartendro/view/admin/debug.py:@app.route('/admin/debug')
ui/bartendro/view/admin/liquidlevel.py:@app.route('/admin/liquidlevel')
ui/bartendro/view/admin/report.py:@app.route('/admin/report')
ui/bartendro/view/admin/report.py:@app.route('/admin/report/<begin>/<end>')
ui/bartendro/view/root.py:@app.route('/')
ui/bartendro/view/root.py:@app.route('/shots')
ui/bartendro/view/root.py:@app.route('/graphical_shots')
ui/bartendro/view/drink/drink.py:@app.route('/drink/<int:id>')
ui/bartendro/view/drink/drink.py:@app.route('/drink/<int:id>/go')
ui/bartendro/view/drink/drink.py:@app.route('/drink/sobriety')
ui/bartendro/view/drink/drink.py:@app.route('/drink/all')
ui/bartendro/view/drink/drink.py:@app.route('/drink/available')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/dispenser/<int:disp>/on')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/dispenser/<int:disp>/on/reverse')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/dispenser/<int:disp>/off')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/dispenser/<int:disp>/test')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/clean')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/clean/right')
ui/bartendro/view/ws/dispenser.py:@app.route('/ws/clean/left')
ui/bartendro/view/ws/misc.py:@app.route('/ws/reset')
ui/bartendro/view/ws/misc.py:@app.route('/ws/test')
ui/bartendro/view/ws/misc.py:@app.route('/ws/checklevels')
ui/bartendro/view/ws/misc.py:@app.route('/ws/download/bartendro.db')
ui/bartendro/view/ws/option.py:@app.route('/ws/options', methods=["POST", "GET"])
ui/bartendro/view/ws/option.py:@app.route('/ws/upload', methods=["POST"])
ui/bartendro/view/ws/option.py:@app.route('/ws/upload/confirm', methods=["POST"])
ui/bartendro/view/ws/booze.py:@app.route('/ws/booze/match/<str>')
ui/bartendro/view/ws/drink.py:@app.route('/ws/drink/<int:drink>')
ui/bartendro/view/ws/drink.py:@app.route('/ws/drink/custom')
ui/bartendro/view/ws/drink.py:@app.route('/ws/drink/<int:drink>/available/<int:state>')
ui/bartendro/view/ws/drink.py:@app.route('/ws/shots/<int:booze_id>')
ui/bartendro/view/ws/drink.py:@app.route('/ws/drink/<int:id>/load')
ui/bartendro/view/ws/drink.py:@app.route('/ws/drink/<int:drink>/save', methods=["POST"])
ui/bartendro/view/ws/liquidlevel.py:@app.route('/ws/liquidlevel/test/<int:disp>')
ui/bartendro/view/ws/liquidlevel.py:@app.route('/ws/liquidlevel/out/<int:disp>/set')
ui/bartendro/view/ws/liquidlevel.py:@app.route('/ws/liquidlevel/low/<int:disp>/set')
ui/bartendro/view/ws/liquidlevel.py:@app.route('/ws/liquidlevel/out/all/set')
ui/bartendro/view/ws/liquidlevel.py:@app.route('/ws/liquidlevel/low/all/set')



# Bartendro software notes Mon Feb 11 15:49:36 PST 2019


Goal? It would be nice to be able to have features from the bartendro software.

Notes:
sqlite3 bartendro.db

see options, including password
select * from option;
username: bartendro
password (default): boozemeup

class Mixer in mixer.py is the point of it all..
'''The mixer object is the heart of Bartendro. This is where the state of the bot
is managed, checked if drinks can be made, and actually make drinks. Everything
else in Bartendro lives for *this* *code*. :) '''

bartendro
/Users/richgibson/wa/pistonbot/bartendro/ui

 ./bartendro_server.py --debug

To Add a view

in bartendro/ui/bartendro/view
cp booze.py snooze.py

in bartendro/ui/bartendro
edit __init__.py
from bartendro.view import snooze

edit 
 @app.route('/booze')
 @login_required
 def booze():

templates in 
bartendro/ui/content/templates

cp booze snooze
edit snooze

http://127.0.0.1:8080/snooze

Yay! That worked.
Next: add an endpoint which talks to my pumps.

the bartendro has a restfulish api. yay.

/ws/drink/34?booze1=60&booze24=10&booze28=20&booze8=50
/ws/drink/[drink id]?booze[booze id]=[qty ml]&booze24=10&...

booze[booze.id]=[qty in ml]
booze1 = booze id=1, vodka
booze24 = booze id=24, triple sec

The quantity is in ml

I think I can hack my pumps in in ws/drink.py ws_make_drink()
rather than app.mixer.make_drink(drink, recipe)

from bartendro import app
from bartendro import mixer
from bartendro import db
from bartendro.model.drink import Drink
from bartendro.model.drink import DrinkName
drink = Drink.query.filter_by(id=1)[0]
drink
<Drink>(1,Sour Apple Martini,A fruity martini made with tart apple pucker and vodka. Stir or shake after it's dispensed.,<DrinkBooze>(1) <DrinkBooze>(2))>
# mixer object normally requires driver and mc - but in my hacked world...
# this almost works, for large values of 'almost'
mix=mixer.Mixer(None,None)


The question is: how much do I want to hack it?
- a custom app.mixer.py
- hack /ui/bartendro/view/ws/drink.py


app.mixer.dispense_shot
app.mixer.make_drink


--
- made hello_drinkbot branch on my git hub
- checked it out on pi
- to install dependencies
```pip install -r requirements.txt```
- to start bartendro
```./bartendro_server.py --debug```

(need to export :
export BARTENDRO_SOFTWARE_ONLY=1)

specify address
./bartendro_server.py --debug -t 10.1.10.214

now sqlalchemy.orm.exc.FlushError
but that is cool. 

```./bartendro_server.py --debug -t 10.1.10.214```
...
I have the code runnnig on the pi except for that sql error. 


Methods from bartendro/ui/bartendro/mixer.py
    def _can_make_drink(self, boozes, booze_dict):
    def _check_liquid_levels(self):
    def _dispense_recipe(self, recipe, always_fast = False):
    def _state_check(self):
    def _state_current_sense(self):
    def _state_error(self):
    def _state_hard_out(self):
    def _state_low(self):
    def _state_out(self):
    def _state_pour_done(self):
    def _state_pouring(self):
    def _state_pre_pour(self):
    def _state_pre_shot(self):
    def _state_ready(self):
    def _state_test_dispense(self):
    def check_levels(self):
    def clean(self):
    def clean_left(self):
    def clean_right(self):
    def dispense_ml(self, dispenser, ml):
    def dispense_shot(self, dispenser, ml):
    def do_event(self, event):
    def get_available_drink_list(self):
    def liquid_level_test(self, dispenser, threshold):
    def make_drink(self, drink, recipe):
    def reset(self):

It may be driver.py /Users/richgibson/wa/pistonbot/bartendro/ui/bartendro/router/driver.py
which we need to mess with.

select count(booze_id), name from drink_booze db, booze bz  where booze_id=bz.id group by name order by name;

