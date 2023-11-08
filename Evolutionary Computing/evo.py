'''
DS3500 Project: TA Resource Allocation with Evolutionary Computing
File that contains evo class framework
4/17/2023
'''

import random as rnd
import copy #used for deep copies
from functools import reduce
import time
import csv
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

#read path
path = Path(__file__).parent

class Evo:
    def __init__(self):
        self.pop = {} #((obj1, eval1), (obj2, eval2), ...)  ==> solution
        # solutions that are more fit are better adapted
        self.fitness = {} # name -> objective function
        #agents of change
        self.agents = {} #name -> (agent operator, # input solutions)

    def size(self):
        ''' The size of the solution population'''
        return len(self.pop)

    def add_fitness_criteria(self, name, f):
        ''' Registering an objective with the Evo framework
        name - the name of the objective (string)
        f - the objective function: f(solution) --> a number '''
        self.fitness[name] = f

    def add_agent(self, name, op, k=1):
        ''' Registering an agent with the Evo framework
        name - the name of the agent
        op - the operator - the function carried out by the agent op(*solutions) -> new solution
        k - the number of input solutions (usually 1)'''
        self.agents[name] = (op, k)

    def get_random_solutions(self, k=1):
        '''Pick k random solutions from the population as a list of solutions
            We are returning DEEP copies of these solutions as a list'''
        if self.size() == 0: #no solutions in the populations
            return []
        else:
            popvals = tuple(self.pop.values())
            return [copy.deepcopy(rnd.choice(popvals)) for _ in range(k)] #creates a copy so that change can be applied onto it

    def add_solution(self, sol):
        ''' Add new solution to the population '''
        eval = tuple([(name, f(sol)) for name, f in self.fitness.items()])
        self.pop[eval] = sol

    def run_agent(self, name):
        ''' Invoke an agent against the current population '''
        op, k = self.agents[name]
        picks = self.get_random_solutions(k)
        new_solution = op(picks)
        self.add_solution(new_solution)

    def evolve(self, runLength = 10, dom=100, status = 100, sync = 1000):
        '''To run n random agents against the population
        n   - # of agent invocations
        dom - # of iterations between discarding the dominated solutions '''
        # set timer
        duration = runLength * 60
        startTime = time.time()
        agent_names = list(self.agents.keys())
        i = 0
        while (time.time() - startTime) < duration:
            i += 1
            pick = rnd.choice(agent_names)  # pick an agent to run
            self.run_agent(pick)
            if i % dom == 0:
                self.remove_dominated()

            if i % status == 0:  # print the population
                self.remove_dominated()
                print("Iteration: ", i)
                print("Population Size: ", self.size())
                print(self)

            if i % sync == 0:
                try:
                    with open('solutions.dat', 'rb') as file:
                        #load saved pop into a dictionary obj
                        loaded = pickle.load(file)

                        #merge loaded solutions into my population
                        for eval, sol in loaded.items():
                            self.pop[eval] = sol
                except Exception as e:
                    print(e)

                #remove the dominated solutions
                self.remove_dominated()
                #resave the non-dominated solutions back to the file
                with open('solutions.dat', 'wb') as file:
                    pickle.dump(self.pop,file)
        # Clean up population
        self.remove_dominated()

    @staticmethod
    def _dominates(p,q):
        pscores = [score for _, score in p]
        qscores = [score for _, score in q]
        score_diffs = list(map(lambda x, y: y-x, pscores, qscores))
        min_diff = min(score_diffs)
        max_diff = max(score_diffs)
        return min_diff >= 0.0 and max_diff > 0.0

    @staticmethod
    def _reduce_nds(S, p):
        return S - {q for q in S if Evo._dominates(p,q)}

    def remove_dominated(self):
        nds = reduce(Evo._reduce_nds, self.pop.keys(), self.pop.keys())
        self.pop = {k:self.pop[k] for k in nds}

    def __str__(self):
        """ Output the solutions in the population """
        rslt = ""
        for eval,sol in self.pop.items():
            rslt += str(dict(eval))+":\n"+str(sol)+"\n"
        return rslt

    def csvOutput(self):
        ''' Output objective scores to a csv file'''
        with open(path / 'results/summary.csv', 'w', newline='') as file:
            solNum = 1
            writer = csv.writer(file)
            writer.writerow(['solutions','overallocation','conflicts','undersupport','unwilling','unpreferred'])
            for eval in self.pop.keys():
                evalDict = dict(eval)
                writer.writerow([f'solution{solNum}',evalDict['overallocation'],evalDict['conflicts'],evalDict['undersupport'],evalDict['unwilling'],evalDict['unpreferred']])
                solNum += 1

    def best_solution_output(self):
        """Output top scores to a csv file"""
        bestSols = dict()
        scores = pd.read_csv(path / 'results/summary.csv')
        scores = scores[['overallocation','conflicts','undersupport','unwilling','unpreferred']]
        scores = scores[(scores.conflicts == 0) & (scores.unwilling==0)]
        solNum = 1
        for eval in self.pop.keys():
            evalDict = dict(eval)
            #print(evalDict['overallocation'])
            for index, row in scores.iterrows():
                #print(row['overallocation'])
                if (row['overallocation'] == evalDict['overallocation']) and (row['conflicts'] == evalDict['conflicts']) \
                        and (row['undersupport'] == evalDict['undersupport']) and (row['unwilling'] == evalDict['unwilling']) \
                        and (row['unpreferred'] == evalDict['unpreferred']):
                    bestSols[solNum] = self.pop[eval]
            solNum += 1
        for i in bestSols.keys():
            np.savetxt(path / f'results/best_solutions{i}.csv', bestSols[i],delimiter=',')










