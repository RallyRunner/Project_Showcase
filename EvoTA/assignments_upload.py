'''
DS3500 Project: TA Resource Allocation with Evolutionary Computing
-File that takes inputs of dataframes and runs evo.py
4/17/2023
'''
#import necessary libraries
from evo import Evo
import random as rnd
import numpy as np
import pandas as pd
from numpy import copy
import streamlit as st


def overallocation(solution):
    ''' Objective: Sum overallocation penalty over all TAs
        Overallocation / TA: numAssigned - maxAssigned = overallocation '''
    numAssigned = np.sum(solution, axis = 1) #sums across the row
    overallocated = np.subtract(numAssigned, maxAssigned)
    overallocated = np.sum(overallocated[overallocated > 0]) #negative allocation does not matter
    return overallocated

def conflicts(solution):
    ''' Objective: Sum time conflicts over all TAs
        conflict: when a TA has two labs meeting at the same time (need to look into daytime)
        only count 1 conflict for TA'''
    #create a deep copy of solution to replace values
    tempSolution = copy(solution)
    tempSolution = tempSolution.astype(str)

    #find coords of array where value = 1 to replace with schedule dictionary
    coords = zip(np.where(tempSolution == '1')[0], np.where(tempSolution == '1')[1])
    for x,y in coords:
        tempSolution[x][y] = sectionSchedules[y]

    #conflict array setup to fill with true false values based on if repeated schedules exist
    conflictArr = np.zeros(tempSolution.shape[0], dtype=bool)
    #for each row in substituted Solution
    for i, row in enumerate(tempSolution):
        #pick out nonzero elements of row
        nonZero = row[row != '0']
        #check if repeated length is same
        if len(nonZero) != len(set(nonZero)):
            conflictArr[i] = True #identifies which rows have conflicts
    return np.sum(conflictArr[conflictArr == True])

def undersupport(solution):
    ''' Objective: Count undersupport penalty over all TAs
        undersupport: min_ta - numAssigned = undersupport'''
    #find the number assigned to each section
    numAssigned = np.sum(solution, axis = 0)
    undersupported = np.subtract(sectionTA[:,0], numAssigned)
    # only need positive values b/c over assigning doesn't matter
    undersupported = np.sum(undersupported[undersupported > 0])
    return undersupported

def convertPreference(tasArr):
    ''' Function that takes in the TA preference array and converts the following:
        U -> 0
        W -> 1
        P -> 2'''
    tasArr[tasArr == 'U'] = 0
    tasArr[tasArr == 'W'] = 1
    tasArr[tasArr == 'P'] = 2
    return tasArr

def unwilling(solution):
    ''' Objective: Count unwilling penalty over all TAs
        unwilling: when a TA is unwilling (U) to support a section, but is selected for that section'''
    #compare two arrays
    unwillingArr = (solution>tasArrConverted)
    #count the trues
    unwillingCount = np.sum(unwillingArr[unwillingArr == True])
    return unwillingCount

def unpreferred(solution):
    ''' Objective: count slots that aren't preferred over all TAs (count willing slots but not preferred)'''
    #temp change solution 0 vals to arbitrary number so 0s won't get compared
    tempSolution = copy(solution)
    tempSolution[tempSolution == 0] = 5
    #compare two arrays
    unpreferredArr = (tempSolution==tasArrConverted)
    #count the trues
    unpreferredCount = np.sum(unpreferredArr[unpreferredArr == True])
    return unpreferredCount

""" Functions of agents that address objectives """

def agentOA(solutions):
    ''' agent to minimize overallocation'''
    #picks solution
    solution = solutions[0]

    #loops through rows of the solution array
    for i,row in enumerate(solution):
        # identify where 1s are present
        oneIndices = np.where(row==1)[0]
        #if there are more 1s than the maxAssigned for that TA (makes sure that OA is at a minimum)
        if len(oneIndices) > maxAssigned[i]:
            #randomly select maxAssigned[i] indices from the oneIndices
            replaceIndices = np.random.choice(oneIndices, size=maxAssigned[i], replace=False)
            #replace the 1s with 0s
            solution[i, replaceIndices] = 0
    return solution

def agentUS(solutions):
    ''' agent to minimize undersupport'''
    solution = solutions[0]
    #for each column in the solution array
    for i in range(solution.shape[1]):
        #find the indices of 1,0s in the column
        oneIndices = np.where(solution[:, i] == 0)[0]
        zeroIndices = np.where(solution[:, i] == 1)[0]
        #if there are less than minTA val of sectionTA
        if len(oneIndices) < sectionTA[:,0][i]:
            #randomly select x indices from zeroIndices
            replaceIndices = np.random.choice(zeroIndices, size = sectionTA[:,0][i], replace = False)
            #replace the 0s with 1s
            solution[replaceIndices, i] = 1
    return solution

def agentUW(solutions):
    '''Agent to minimize unwilling'''
    solution = solutions[0]
    unwilling = (solution > tasArrConverted)
    solution[unwilling == True] = 0
    return solution

def agentUP(solutions):
    '''Agent to minimize unpreferred by maximizing preferred slots for each TA
        preferred : spots in tasArrConverted == 2'''
    solution = solutions[0]
    solution[tasArrConverted == 2] = 1
    return solution

def agentSwap(solutions):
    """Agent to try to create some random swapping within the solution"""
    solution = solutions[0]
    #define size of square to be swapped
    n = 3
    #generate two random indicies for top left corner of each square
    i1, j1 = np.random.randint(0, solution.shape[0]-n+1), np.random.randint(0, solution.shape[1]-n+1)
    i2, j2 = np.random.randint(0, solution.shape[0] - n + 1), np.random.randint(0, solution.shape[1] - n + 1)

    #swawp the two squares
    temp = np.copy(solution[i1:i1+n, j1:j1+n])
    solution[i1:i1 + n, j1:j1 + n] = solution[i2:i2 + n, j2:j2 + n]
    solution[i2:i2+n, j2:j2+n] = temp
    return solution

def main(sectionData, taData):
    #read data in
    '''Read section data -> need to read for min_ta & max_ta // sections that overlap in time'''
    sectionDf = pd.DataFrame(sectionData)
    sectionDf = sectionDf[['section', 'daytime', 'min_ta', 'max_ta']]
    global sectionTA
    sectionTA = sectionDf[['min_ta', 'max_ta']].to_numpy()

    # sections and their schedules
    global sectionSchedules
    sectionSchedules = {section: schedule for section, schedule in zip(sectionDf['section'], sectionDf['daytime'])}

    '''Read TA data'''
    tasDf = pd.DataFrame(taData)
    global maxAssigned
    maxAssigned = tasDf['max_assigned'].to_numpy()

    # keep plain ta preference array
    tasDf = tasDf.drop(['max_assigned', 'ta_id', 'name'], axis=1)
    global tasArr
    tasArr = tasDf.to_numpy()

    # convert preferences to 0,1,2
    global tasArrConverted
    tasArrConverted = convertPreference(tasArr)

    # create framework
    E = Evo()

    # register some objectives
    E.add_fitness_criteria("overallocation", overallocation)
    E.add_fitness_criteria("conflicts", conflicts)
    E.add_fitness_criteria("undersupport", undersupport)
    E.add_fitness_criteria("unwilling", unwilling)
    E.add_fitness_criteria("unpreferred", unpreferred)

    # register some agents
    E.add_agent("agentOA", agentOA, k=1)
    E.add_agent("agentUS", agentUS, k=1)
    E.add_agent("agentUW", agentUW, k=1)
    E.add_agent('agentUP', agentUP, k=1)
    E.add_agent('agentSwap',agentSwap,k=1)

    # seed the population with an initial random solution
    rng = np.random.default_rng()
    L = rng.choice([0,1], size=(tasArr.shape[0],tasArr.shape[1]))
    E.add_solution(L)
    print(E)

    # run the evolver(runlength (in mins), dom, status)
    #replaced n iterations with run length
    E.evolve(1.5,100, 10000)

    # print final results
    print(E)

    #output results into a csv
    E.csvOutput()
    E.best_solution_output()

if __name__ == '__main__':
    main()