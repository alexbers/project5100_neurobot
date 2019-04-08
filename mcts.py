# Forked from https://github.com/suragnair/alpha-zero-general

import math
import copy
import random
import numpy as np
EPS = 1e-8

import game

class MCTS():
    """
    This class handles the MCTS tree.
    """

    def __init__(self, nnet, args):
        self.nnet = nnet
        self.args = args

    def getActionProb(self, canonicalBoard, temp=1):
        """
        This function performs numMCTSSims simulations of MCTS starting from
        canonicalBoard.

        Returns:
            probs: a policy vector where the probability of the ith action is
                   proportional to Nsa[(s,a)]**(1./temp)
        """

        self.Qsa = {}       # stores Q values for s,a (as defined in the paper)
        self.Nsa = {}       # stores #times edge s,a was visited
        self.Ns = {}        # stores #times board s was visited
        self.Ps = {}        # stores initial policy (returned by neural net)

        self.Es = {}        # stores game.getGameEnded ended for board s
        self.Vs = {}        # stores game.getValidMoves for board s

        self.sa = {}        # stores next s for s,a

        # only one turn case
        valid = game.getValidMoves(canonicalBoard, 1)
        if sum(valid) == 1:
            bestA = np.argmax(valid)
            probs = [0]*len(valid)
            probs[bestA]=1
            return probs


        canonicalBoard = copy.deepcopy(canonicalBoard)

        # hide enemy cards
        canonicalBoard.enemyCardsAvailable = [0] * 16
        for i in random.sample(range(16), 5):
            canonicalBoard.enemyCardsAvailable[i] = 1

        # force equal conditions for the opponents
        if canonicalBoard.turn_number % 2 == 0:
            canonicalBoard.turn_number += 1

        canonicalBoard.myNextA = None
        canonicalBoard.enemyNextA = None            

        for i in range(self.args["numMCTSSims"]):
            # print("=========== NEW TRY ========")
            self.search(canonicalBoard)

        s = game.stringRepresentation(canonicalBoard)
        counts = [self.Nsa[(s,a)] if (s,a) in self.Nsa else 0 for a in range(game.getActionSize())]
        #print(counts)
        if sum(counts) == 0:
            return [0]*len(counts)

        if temp==0:
            bestA = np.argmax(counts)
            probs = [0]*len(counts)
            probs[bestA]=1
            return probs

        counts = [x**(1./temp) for x in counts]
        probs = [x/float(sum(counts)) for x in counts]
        return probs


    def search(self, canonicalBoard, depth=0):
        """
        This function performs one iteration of MCTS. It is recursively called
        till a leaf node is found. The action chosen at each node is one that
        has the maximum upper confidence bound as in the paper.

        Once a leaf node is found, the neural network is called to return an
        initial policy P and a value v for the state. This value is propogated
        up the search path. In case the leaf node is a terminal state, the
        outcome is propogated up the search path. The values of Ns, Nsa, Qsa are
        updated.

        NOTE: the return values are the negative of the value of the current
        state. This is done since v is in [-1,1] and if v is the value of a
        state for the current player, then its value is -v for the other player.

        Returns:
            v: the negative of the value of the current canonicalBoard
        """

        if depth == 1500:
            print("=DEBUG DEPTH=", depth, str(canonicalBoard))

        s = game.stringRepresentation(canonicalBoard)

        if s not in self.Es:
            self.Es[s] = game.getGameEnded(canonicalBoard, 1)

        if self.Es[s]!=0:
            # terminal node
            # print("END")
            return -self.Es[s]

        valids = game.getValidMoves(canonicalBoard, 1)
        if sum(valids) == 1:
            # print("shortcut")
            a = np.argmax(valids)
            if s not in self.Ps:
                self.Ps[s] = valids
                self.Vs[s] = valids
                self.Ns[s] = 0
        else:
            if s not in self.Ps:
                # leaf node
                self.Ps[s], v = self.nnet.predict(canonicalBoard)

                # print("predict result")
                # print(self.Ps[s])
                # print(v)

                # if "disable_skip" in self.args:
                #     self.Ps[s][48] = 0.0
                #     # print("self.Ps[s]", self.Ps[s])
                #     if valids[48] > 0 and np.sum(valids) == 1:
                #         self.Ps[s][48] = 1.0

                # print("canonicalBoard", canonicalBoard, "valids", valids)
                self.Ps[s] = self.Ps[s]*valids      # masking invalid moves
                sum_Ps_s = np.sum(self.Ps[s])
                if sum_Ps_s > 0:
                    self.Ps[s] = self.Ps[s] / sum_Ps_s    # renormalize
                else:
                    # if all valid moves were masked make all valid moves equally probable
                    
                    # NB! All valid moves may be masked if either your NNet architecture is insufficient or you've get overfitting or something else.
                    # If you have got dozens or hundreds of these messages you should pay attention to your NNet and/or training process.   
                    print("All valid moves were masked, do workaround.")
                    print("because valids", valids)
                    print("and self.Ps[s]", self.Ps[s])
                    self.Ps[s] = self.Ps[s] + valids
                    self.Ps[s] = self.Ps[s] / np.sum(self.Ps[s])

                self.Vs[s] = valids
                self.Ns[s] = 0
                # print("value", str(canonicalBoard), -v)
                return -v

            valids = self.Vs[s]
            cur_best = -float('inf')
            best_act = -1

            # pick the action with the highest upper confidence bound
            # print("valids", valids)
            # print("depth", depth)
            # print("canonicalBoard", str(canonicalBoard))

            for a in range(game.getActionSize()):
                if valids[a]:
                    if (s,a) in self.Qsa:
                        u = self.Qsa[(s,a)] + self.args["cpuct"]*self.Ps[s][a]*math.sqrt(self.Ns[s])/(1+self.Nsa[(s,a)])
                    else:
                        u = self.args["cpuct"]*self.Ps[s][a]*math.sqrt(self.Ns[s] + EPS)     # Q = 0 ?

                    if u > cur_best:
                        cur_best = u
                        best_act = a

                    # if not board_history:
                    # print("a", a, "%.3f" % u)

                

            a = best_act
        
        if (s,a) in self.sa:
            next_s = self.sa[(s,a)]
        else:
            next_s, next_player = game.getNextState(canonicalBoard, 1, a)
            next_s = game.getCanonicalForm(next_s, next_player)

            self.sa[(s,a)] = next_s

        # print("best", a)
        # print("next", str(next_s))
        # print()

        v = self.search(next_s, depth + 1)

        if (s,a) in self.Qsa:
            self.Qsa[(s,a)] = (self.Nsa[(s,a)]*self.Qsa[(s,a)] + v)/(self.Nsa[(s,a)]+1)
            self.Nsa[(s,a)] += 1
        else:
            self.Qsa[(s,a)] = v
            self.Nsa[(s,a)] = 1

        self.Ns[s] += 1
        return -v
