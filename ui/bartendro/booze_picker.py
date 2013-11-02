import random
import sys
import time
from threading import Lock, Thread

from deap import base
from deap import creator
from deap import tools

from bartendro import app, db
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze

def evalBoozeSet(individual):
    return app.planner.evalBoozeSet(individual)

def get_random_booze_from_pool():
    return app.planner.get_random_booze_from_pool()

class Planner(Thread):

    def __init__(self, num_dispensers):
        Thread.__init__(self)

        self.lock = Lock()

        # Index data
        self.num_dispensers = num_dispensers
        self.num_boozes = 0
        self.boozes = None
        self.pool = None
        self.boozes_by_id = None

        # Parameters
        self.require_boozes = None
        self.exclude_boozes = None
        self.num_generations = 0

        # Status
        self.done = True
        self.best_set = None
        self.cur_generation = 0

    def is_done(self):
        self.lock.acquire()
        done = self.done
        self.lock.release()

        return done

    def get_best_set(self):
        self.lock.acquire()
        booze_set = self.best_set
        generation = self.cur_generation
        self.lock.release()

        print "best so far: ", booze_set
        if not booze_set:
            return { "boozes" : [], "drinks" : [], "generation" : 0 }

        can_make = self.get_can_make_list(booze_set)

        boozes = []
        for booze_id in booze_set:
            boozes.add((boozes_by_id[booze_id].name, boozes[booze_id].id))

        drinks = []
        for drink in can_make:
            drink_boozes = []
            for drink_booze in drink.drink_boozes:
                drink_boozes.append( { "name" : drink_booze.booze.name, "id" : drink_booze.booze.id })
            drinks[drink.id] = { 'name' : drink.name.name, boozes : drink_boozes }

        return { "boozes" : boozes, "drinks" : drinks, "generation" : generation }

    def evolve(self, require_boozes, exclude_boozes, num_generations):

        self.require_boozes = require_boozes
        self.exclude_boozes = exclude_boozes
        self.num_generations = num_generations
        self.done = False

        self.start()

    def run(self):
        random.seed(int(time.time()))
        self.num_boozes = self.num_dispensers - len(self.require_boozes)

        # load data from the bartendro database
        self.drinks = db.session.query(Drink).order_by(Drink.id).all()
        self.boozes = db.session.query(Booze).order_by(Booze.id).all()
        self.boozes_by_id = {}
        for booze in self.boozes:
            self.boozes_by_id[booze.id] = booze 

        self.create_indexes()

        best_ind = self.genetic_algorithm(self.num_generations)
        for i, item in enumerate(best_ind):
            best_ind[i] = self.boozes[self.pool[item]].id

        best_ind = self.require_boozes + best_ind
        self.done = True

    def create_indexes(self):
        pool = []
        for index, booze in enumerate(self.boozes):
            if booze.id in self.exclude_boozes: continue
            if booze.id in self.require_boozes: continue
            pool.append(index)

        booze_drink_index = {}
        for booze in self.boozes:
            drink_list = []
            for db in booze.drink_booze:
                drink_list.append(db.drink)

            drink_dict = {}
            for drink in drink_list:
                drink_booze_list = []
                for db in drink.drink_boozes:
                    if booze.id == db.booze_id: continue
                    drink_booze_list.append(db.booze_id)
                drink_dict[drink] = drink_booze_list

            booze_drink_index[booze.id] = drink_dict

        self.pool = pool
        self.booze_drink_index = booze_drink_index

    def get_can_make_list(self, booze_set):
        can_make = []
        for booze_id in booze_set:
            for drink in self.booze_drink_index[booze_id].keys():
                ok = True
                other_boozes = self.booze_drink_index[booze_id][drink]
                for other_booze in other_boozes:
                    if not other_booze in booze_set:
                        ok = False
                        break

                if ok: can_make.append(drink)

        return list(set(can_make))

    def evalBoozeSet(self, individual):
        booze_set = []
        for item in individual:
            booze_set.append(self.boozes[self.pool[item]].id)
        booze_set.extend(self.require_boozes)

        return (len(self.get_can_make_list(booze_set)),)

    def get_random_booze_from_pool(self):
        return random.randint(0, len(self.pool) - 1)

    def genetic_algorithm(self, NGEN):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("attr_booze", get_random_booze_from_pool)
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_booze, self.num_boozes)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", evalBoozeSet)
        toolbox.register("mate", tools.cxTwoPoints)
        toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)

        pop = toolbox.population(n=300)
        CXPB, MUTPB, = 0.5, 0.2
        
        # Evaluate the entire population
        fitnesses = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        # Begin the evolution
        for g in range(NGEN):
            
            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(toolbox.clone, offspring))
        
            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
        
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # The population is entirely replaced by the offspring
            pop[:] = offspring
            
            # Gather all the fitnesses in one list and print the stats
            fits = [ind.fitness.values[0] for ind in pop]
            
            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x*x for x in fits)
            std = abs(sum2 / length - mean**2)**0.5

            self.lock.acquire()
            self.cur_generation = g
            self.best_set = tools.selBest(pop, 1)[0]
            self.lock.release()

            print g, self.best_set
        
        return tools.selBest(pop, 1)[0]
