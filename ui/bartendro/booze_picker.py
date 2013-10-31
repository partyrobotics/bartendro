#!/usr/bin/env python

import random
import sys
import time

from deap import base
from deap import creator
from deap import tools

from bartendro import app, db
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze

random.seed(int(time.time()))

num_dispensers = 7

# new features: must have and remove duplicate boozes
exclude_boozes = [ 13, 14, 29, 2, 25, 18, 26, 19, 8, 58 ]
required_boozes = [ 1, 11, 12, 9 ]

num_boozes = num_dispensers - len(required_boozes)

def create_pool(boozes, exclude_boozes, required_boozes):
    pool = []
    for index, booze in enumerate(boozes):
        if booze.id in exclude_boozes: 
            print "    exclude: %s (%d)" % (booze.name, booze.id)
            continue
        if booze.id in required_boozes: 
            print "   required: %s (%d)" % (booze.name, booze.id)
            continue
        print "  available: %s (%d)" % (booze.name, booze.id)
        pool.append(index)

    return pool

def load_booze_index(boozes):
    booze_drink_index = {}
    for booze in boozes:
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

    return booze_drink_index

def print_booze_index(booze_drink_index):
    for booze_id in booze_drink_index.keys():
        print "booze_id: %d" % booze_id
        for drink in booze_drink_index[booze_id].keys():
            print "   %s: " % drink.name.name,
            other_boozes = booze_drink_index[booze_id][drink]
            for b in other_boozes:
                print "%s" % b,
            print

def get_can_make_list(booze_set):
    can_make = []
    for booze_id in booze_set:
        for drink in booze_drink_index[booze_id].keys():
            ok = True
            other_boozes = booze_drink_index[booze_id][drink]
            for other_booze in other_boozes:
                if not other_booze in booze_set:
                    ok = False
                    break

            if ok: can_make.append(drink)

    return list(set(can_make))

def print_booze_set(booze_set):
    can_make = get_can_make_list(booze_set)
    print "Boozes:"
    for booze_id in booze_set:
        print "   %s (id %d)" % (boozes_by_id[booze_id].name, boozes[booze_id].id)

    print "Drinks:"
    for drink in can_make:
        print "   %s: " % drink.name.name,
        tmp = []
        for drink_booze in drink.drink_boozes:
            tmp.append(drink_booze.booze.name)
        print ", ".join(tmp)
    print

def evalBoozeSet(individual):
    booze_set = []
    for item in individual:
        booze_set.append(boozes[pool[item]].id)
    booze_set.extend(required_boozes)

    return (len(get_can_make_list(booze_set)),)

def get_random_booze_from_pool():
    return random.randint(0, len(pool) - 1)

def main():
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_booze", get_random_booze_from_pool)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_booze, num_boozes)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", evalBoozeSet)
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=300)
    CXPB, MUTPB, NGEN = 0.5, 0.2, 16
    
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
        
        print "Generation %i: %s" % (g, max(fits))
    
    best_ind = tools.selBest(pop, 1)[0]
    for i, item in enumerate(best_ind):
        best_ind[i] = boozes[pool[item]].id

    best_ind = required_boozes + best_ind
    print best_ind
    print_booze_set(best_ind)

if __name__ == "__main__":
    # load data from the bartendro database
    drinks = db.session.query(Drink).order_by(Drink.id).all()
    boozes = db.session.query(Booze).order_by(Booze.id).all()
    boozes_by_id = {}
    for booze in boozes:
        boozes_by_id[booze.id] = booze 

    booze_drink_index = load_booze_index(boozes)
    #print_booze_index(booze_drink_index)
    pool = create_pool(boozes, exclude_boozes, required_boozes)

    main()
