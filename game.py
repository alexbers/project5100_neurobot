import copy
import random
import sys
import math

import numpy as np


class Board:
    def __init__(self):
        self.myS = 10000
        self.myB = 200
        self.myM = 0

        self.myCooldown = 0

        # B+ B- BI+ BI- BD+ BD- S+ S- SI+ SI- SD+ SD- IPS+ IPS- Centerer M-
        self.myEffectsTimeLeft = [0] * 16
        self.myCardsAvailable = [0] * 16

        self.enemyS = 10000
        self.enemyB = 200
        self.enemyM = 0

        self.enemyCooldown = 0

        self.enemyEffectsTimeLeft = [0] * 16
        self.enemyCardsAvailable = [0] * 16

        self.turn_number = 0

        for i in random.sample(range(16), 5):
            self.myCardsAvailable[i] = 1

        for i in random.sample(range(16), 5):
            self.enemyCardsAvailable[i] = 1

        self.myNextA = None
        self.enemyNextA = None

    def __str__(self):
        ret = "%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % (self.myS, self.myB, self.myM, 
            self.myCooldown, self.myEffectsTimeLeft, self.myCardsAvailable, self.enemyS, 
            self.enemyB, self.enemyM, self.enemyCooldown, self.enemyEffectsTimeLeft, 
            self.enemyCardsAvailable, self.myNextA, self.enemyNextA, self.turn_number)
        return ret

    def as_float_list(self):
        ret = []
        ret += [self.myS/300000]
        ret += [self.myB/3000]
        ret += [self.myM//1000/5000000]
        ret += [self.myCooldown/16]
        ret += [t/6 for t in self.myEffectsTimeLeft]
        ret += self.myCardsAvailable

        ret += [self.enemyS/300000]
        ret += [self.enemyB/3000]
        ret += [self.enemyM//1000/5000000]
        ret += [self.enemyCooldown/16]
        ret += [t/6 for t in self.enemyEffectsTimeLeft]

        return np.array(ret)


    def applyActionEffects(self):
        myA = self.myNextA
        enemyA = self.enemyNextA

        self.myNextA = None
        self.enemyNextA = None

        if myA is not None:
            if 0 <= myA < 16:
                if myA in [0, 1, 6, 7, 14, 15]:
                    self.myEffectsTimeLeft[myA] = 1
                elif myA in [8]:
                    self.myEffectsTimeLeft[myA] = 4
                elif myA in [12]:
                    self.myEffectsTimeLeft[myA] = 12
                else:
                    self.myEffectsTimeLeft[myA] = 5
                new_card = random.choice([i for i in range(16) if self.myCardsAvailable[i] == 0])
                self.myCardsAvailable[myA] = 0
                self.myCardsAvailable[new_card] = 1

                self.myCooldown = 6 if (myA) != 14 else 16
            elif 16 <= myA < 32:
                if myA-16 in [0, 1, 6, 7, 14, 15]:
                    self.enemyEffectsTimeLeft[myA-16] = 1
                elif myA-16 in [8]:
                    self.enemyEffectsTimeLeft[myA-16] = 4
                elif myA-16 in [12]:
                    self.enemyEffectsTimeLeft[myA-16] = 12
                else:
                    self.enemyEffectsTimeLeft[myA-16] = 5

                new_card = random.choice([i for i in range(16) if self.myCardsAvailable[i] == 0])
                self.myCardsAvailable[myA-16] = 0
                self.myCardsAvailable[new_card] = 1

                self.myCooldown = 6 if (myA - 16) != 14 else 16
            elif 32 <= myA < 48:
                new_card = random.choice([i for i in range(16) if self.myCardsAvailable[i] == 0])
                self.myCardsAvailable[myA-32] = 0
                self.myCardsAvailable[new_card] = 1
                self.myCooldown = 3

        if enemyA is not None:
            # the same, but vice versa
            if 0 <= enemyA < 16:
                if enemyA in [0, 1, 6, 7, 14, 15]:
                    self.enemyEffectsTimeLeft[enemyA] = 1
                elif enemyA in [8]:
                    self.enemyEffectsTimeLeft[enemyA] = 4
                elif enemyA in [12]:
                    self.enemyEffectsTimeLeft[enemyA] = 12
                else:
                    self.enemyEffectsTimeLeft[enemyA] = 5

                new_card = random.choice([i for i in range(16) if self.enemyCardsAvailable[i] == 0])
                self.enemyCardsAvailable[enemyA] = 0
                self.enemyCardsAvailable[new_card] = 1

                self.enemyCooldown = 6 if (enemyA) != 14 else 16
            elif 16 <= enemyA < 32:
                if enemyA-16 in [0, 1, 6, 7, 14, 15]:
                    self.myEffectsTimeLeft[enemyA-16] = 1
                elif enemyA-16 in [8]:
                    self.myEffectsTimeLeft[enemyA-16] = 4
                elif enemyA-16 in [12]:
                    self.myEffectsTimeLeft[enemyA-16] = 12
                else:
                    self.myEffectsTimeLeft[enemyA-16] = 5

                new_card = random.choice([i for i in range(16) if self.enemyCardsAvailable[i] == 0])
                self.enemyCardsAvailable[enemyA-16] = 0
                self.enemyCardsAvailable[new_card] = 1

                self.enemyCooldown = 6 if (enemyA - 16) != 14 else 16
            elif 32 <= enemyA < 48:
                new_card = random.choice([i for i in range(16) if self.enemyCardsAvailable[i] == 0])
                self.enemyCardsAvailable[enemyA-32] = 0
                self.enemyCardsAvailable[new_card] = 1
                self.enemyCooldown = 3


    def calc_next_round(self):
        mySI = 1.1
        myBI = 0.04
        mySD = 0.0005
        myBD = 0.8
        myIPS = 1000

        enemySI = 1.1
        enemyBI = 0.04
        enemySD = 0.0005
        enemyBD = 0.8
        enemyIPS = 1000

        self.applyActionEffects()

        if self.myEffectsTimeLeft[0]:
            self.myB += 20
        if self.myEffectsTimeLeft[1]:
            self.myB -= 10
        if self.myEffectsTimeLeft[2]:
            myBI = myBI * 1.35
        if self.myEffectsTimeLeft[3]:
            myBI = myBI * 0.65
        if self.myEffectsTimeLeft[4]:
            myBD = myBD * 1.1
        if self.myEffectsTimeLeft[5]:
            myBD = myBD * 0.92
        if self.myEffectsTimeLeft[6]:
            self.myS += 1000
        if self.myEffectsTimeLeft[7]:
            self.myS -= 500
        if self.myEffectsTimeLeft[8]:
            mySI *= 1.05
        if self.myEffectsTimeLeft[9]:
            mySI *= 0.96
        if self.myEffectsTimeLeft[10]:
            mySD *= 1.30
        if self.myEffectsTimeLeft[11]:
            mySD *= 0.70
        if self.myEffectsTimeLeft[12]:
            myIPS *= 2.0
        if self.myEffectsTimeLeft[13]:
            myIPS *= 0.75
        if self.myEffectsTimeLeft[14]:
            if self.myS > 15000 and self.myB > 200:
                self.myS //= 2
                self.myB //= 2
        if self.myEffectsTimeLeft[15]:
            self.myM -= 100000000


        myS_old = self.myS
        myB_old = self.myB
        self.myS = int(myS_old*mySI - myB_old*myS_old*mySD)
        self.myB = max(0, math.ceil(myB_old*myBD + myB_old*myS_old*mySD*myBI))
        self.myM = self.myM + myS_old*myIPS

        if self.enemyEffectsTimeLeft[0]:
            self.enemyB += 20
        if self.enemyEffectsTimeLeft[1]:
            self.enemyB -= 10
        if self.enemyEffectsTimeLeft[2]:
            enemyBI = enemyBI * 1.35
        if self.enemyEffectsTimeLeft[3]:
            enemyBI = enemyBI * 0.65
        if self.enemyEffectsTimeLeft[4]:
            enemyBD = enemyBD * 1.1
        if self.enemyEffectsTimeLeft[5]:
            enemyBD = enemyBD * 0.92
        if self.enemyEffectsTimeLeft[6]:
            self.enemyS += 1000
        if self.enemyEffectsTimeLeft[7]:
            self.enemyS -= 500
        if self.enemyEffectsTimeLeft[8]:
            enemySI *= 1.05
        if self.enemyEffectsTimeLeft[9]:
            enemySI *= 0.96
        if self.enemyEffectsTimeLeft[10]:
            enemySD *= 1.30
        if self.enemyEffectsTimeLeft[11]:
            enemySD *= 0.70
        if self.enemyEffectsTimeLeft[12]:
            enemyIPS *= 2.0
        if self.enemyEffectsTimeLeft[13]:
            enemyIPS *= 0.75
        if self.enemyEffectsTimeLeft[14]:
            if self.enemyS > 15000 and self.enemyB > 200:
                self.enemyS //= 2
                self.enemyB //= 2
        if self.enemyEffectsTimeLeft[15]:
            self.enemyM -= 100000000

        enemyS_old = self.enemyS
        enemyB_old = self.enemyB
        self.enemyS = int(enemyS_old*enemySI - enemyB_old*enemyS_old*enemySD)
        self.enemyB = max(0, math.ceil(enemyB_old*enemyBD + enemyB_old*enemyS_old*enemySD*enemyBI))
        self.enemyM = self.enemyM + enemyS_old*enemyIPS

        # recalc cooldowns
        self.myCooldown = max(0, self.myCooldown-1)
        self.enemyCooldown = max(0, self.enemyCooldown-1)

        self.myEffectsTimeLeft = [max(0, self.myEffectsTimeLeft[i]-1) for i in range(len(self.myEffectsTimeLeft))]
        self.enemyEffectsTimeLeft = [max(0, self.enemyEffectsTimeLeft[i]-1) for i in range(len(self.enemyEffectsTimeLeft))]


def getInitBoard():
    return Board()

def getActionSize():
    return 16 + 16 + 16 + 1

def getNextState(board, player, action):
    ret_b = copy.deepcopy(board)
    
    if player == 1:
        ret_b.myNextA = action
    else:
        ret_b.enemyNextA = action

    ret_b.turn_number += 1
    if ret_b.turn_number % 2 == 0:
        ret_b.calc_next_round()

    return (ret_b, -player)


def getValidMoves(board, player):
    ret = [0] * getActionSize() # skip move is always available
    ret[16+16+16]  = 1
    if player == 1:
        if board.myCooldown != 0:
            return ret

        for i in range(len(board.myCardsAvailable)):
            if board.myCardsAvailable[i]:
                ret[i] = 1
                ret[i+16] = 1
                ret[i+32] = 1
    else:
        if board.enemyCooldown != 0:
            return ret

        for i in range(len(board.enemyCardsAvailable)):
            if board.enemyCardsAvailable[i]:
                ret[i] = 1
                ret[i+16] = 1
                ret[i+32] = 1
    return ret


def getGameEnded(board, player):
    WIN_M = 5000000000
    if player == 1:
        if board.myS <= 0:
            return -1
        elif board.enemyS <= 0:
            return 1

        if board.myM >= WIN_M:
            return 1
        elif board.enemyM >= WIN_M:
            return -1

        if board.turn_number > 1400:
            return 0.000001
    else:
        if board.myS <= 0:
            return 1
        elif board.enemyS <= 0:
            return -1

        if board.myM >= WIN_M:
            return -1
        elif board.enemyM >= WIN_M:
            return 1

        if board.turn_number > 1400:
            return 0.000001

    return 0


def getCanonicalForm(board, player):
    if player == 1:
        return board
    else:
        b = copy.deepcopy(board)
        b.myS, b.enemyS = b.enemyS, b.myS
        b.myB, b.enemyB = b.enemyB, b.myB
        b.myM, b.enemyM = b.enemyM, b.myM
        b.myCooldown, b.enemyCooldown = b.enemyCooldown, b.myCooldown
        b.myEffectsTimeLeft, b.enemyEffectsTimeLeft = b.enemyEffectsTimeLeft, b.myEffectsTimeLeft
        b.myCardsAvailable, b.enemyCardsAvailable = b.enemyCardsAvailable, b.myCardsAvailable
        b.myNextA, b.enemyNextA = b.enemyNextA, b.myNextA
        return b
    

def stringRepresentation(board):
    return str(board)


def display(board):
    EFFECTS = [
        "B+", "B-", "BI+", "BI-", "BD+",
        "BD-", "S+", "S-", "SI+", "SI-",
        "SD+", "SD-", "IPS+", "IPS-", "Centerer", "M-"
    ]

    print(" -------- turn %s --------------- " % board.turn_number)
    print("P1:")
    print(" S=%s B=%s M=%s" % (board.myS, board.myB, board.myM))
    print(" Cooldown:", board.myCooldown)
    

    for i in range(len(board.myEffectsTimeLeft)):
        if board.myEffectsTimeLeft[i]:
            print(" %s: %s" % (EFFECTS[i], board.myEffectsTimeLeft[i]))

    for i in range(len(board.myCardsAvailable)):
        if board.myCardsAvailable[i]:
            print(EFFECTS[i], end=",")

    print("\nP2:")
    print(" S=%s B=%s M=%s" % (board.enemyS, board.enemyB, board.enemyM))
    print(" Cooldown:", board.enemyCooldown)
    

    for i in range(len(board.enemyEffectsTimeLeft)):
        if board.enemyEffectsTimeLeft[i]:
            print(" %s: %s" % (EFFECTS[i], board.enemyEffectsTimeLeft[i]))

    for i in range(len(board.enemyCardsAvailable)):
        if board.enemyCardsAvailable[i]:
            print(EFFECTS[i], end=",")
    
    print("\n   -----------------------")
