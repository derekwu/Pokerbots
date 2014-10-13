import argparse
import socket
import sys
import pbots_calc
import preflop
import random
import math

"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""
#EQ function:
def EQcalc(hands,board,trash,iters=1000):
    return pbots_calc.calc(hands,board,trash,iters=1000)

class Player:

    def __init__ (self):

        # NEWGAME config (changed only once)
        self.yourName = ""
        self.oppName = ""
        self.stackSize = 0
        self.bb = 0
        self.numHands = 0
        self.timeBank = 0.0
        
        # NEWHAND config (updated every single hand)
        self.handID = 0
        self.button = False #default value
        self.hand3 = [] #current starting hand
        self.hand2 = [] #2 card ending hand, if applicable
        self.discardCard = ""
        self.hand2EQ = 0 #EQ of hand2 after discard
        self.yourBank = 0 #current bank balances
        self.oppBank = 0
        #self.pastActions = {"PREFLOP":[],"FLOP":[],"TURN":[],"RIVER":[]}
        #self.pastActionsT = {"PREFLOP":[None],"FLOP":[None],"TURN":[None],"RIVER":[None]} 
        self.yourPastActions = []
        self.oppPastActions = []
        self.pastActions = []
        self.yourPastActionsH = [None]
        self.oppPastActionsH = [None]
        self.pastActionsH = [None]
        
        # other variables
        self.potSizes = []
        self.potSizesH = [None] 
        self.yourBankH = [None] #your bank history (index starts at 1!)
        self.oppBankH = [None] #nested list, each list has bank history over course of hand
        self.numBoardCards = 0
        self.boardCards = []
        
        
        #tracks opponents playing style:
        
        self.oppPreflopRaises = []
        self.oppAveragePreflopRaise = 0
        
        self.oppCheckToYourPreflopCallRatio = [0.0,0.0] #oppchecks, yourpreflop calls
        self.checkAfterPreflopCall = 0
        self.raiseAfterPreflopCall = 0

        self.buttonRaiseFoldRatio = [0.0,0.0]
        self.buttonRaiseCallRatio = [0.0,0.0]
        self.buttonRaiseRaiseRatio = [0.0,0.0]
        self.foldAfterPreflopRaise = 0
        self.callAfterPreflopRaise = 0
        self.raiseAfterPreflopRaise = 0
        
        self.BBcounter = 0
        self.BBCRcounter = 0
        self.BBRRcounter = 0
        self.numFoldAfterBB = 0.0
        self.numCallAfterBB = 0.0
        self.numRaiseAfterBB = 0.0
        self.numCallRaiseFoldAfterBB = 0.0
        self.numCallRaiseCallAfterBB = 0.0
        self.numCallRaiseRaiseAfterBB = 0.0
        self.numRaiseRaiseRaiseAfterBB = 0.0
        
        self.BBfold = 0.0
        self.BBcall = 0.0
        self.BBraise = 0.0
        self.BBcallRaiseFold = 0.0
        self.BBcallRaiseCall = 0.0
        self.BBcallRaiseRaise = 0.0
        self.BBraiseRaiseRaise = 0.0
        
        self.numOppFlop = 0.0
        self.numOppTurn = 0.0
        self.numOppRiver = 0.0
        self.numOppShow = 0.0
        self.oppFlop = 0.0
        self.oppTurn = 0.0
        self.oppRiver = 0.0
        self.oppShow = 0.0
        
        self.betcounter = [0.0,0.0,0.0]
        self.callcounter = [0.0,0.0,0.0]
        self.counter = [0.0,0.0,0.0]
        self.CRcounter = [0.0,0.0,0.0]
        self.RRcounter = [0.0,0.0,0.0]
        self.firstBetFold = [0.0,0.0,0.0]
        self.firstBetCall = [0.0,0.0,0.0]
        self.firstBetRaise = [0.0,0.0,0.0]
        self.firstCallCheck = [0.0,0.0,0.0]
        self.firstCallRaise = [0.0,0.0,0.0]
        
        self.secondCheck = [0.0,0.0,0.0] #they check
        self.secondRaise = [0.0,0.0,0.0]
        self.secondCheckRaiseFold = [0.0,0.0,0.0]
        self.secondCheckRaiseCall = [0.0,0.0,0.0]
        self.secondCheckRaiseRaise = [0.0,0.0,0.0]
        self.secondRaiseRaiseRaise = [0.0,0.0,0.0]
        
        self.command = ""

    def getCommand(self):
        # Retrieves action command to send
        return self.command
    
    def clearCommand(self):
        self.command = ""

    def parse(self, data):
        # This function takes in packets, parses it, and returns a boolean
        # denoting to send an action or not
        msg = data.split()
        word = msg[0]

        if word == "NEWGAME":
            self.configGame(msg)
            return False
        
        elif word == "NEWHAND":
            self.configHand(msg)
            return False
        
        elif word == "GETACTION":
            self.getAction(msg)
            return True

        elif word == "HANDOVER":
            self.handOver(msg)
            return False

        elif word == "KEYVALUE":
            self.storeKey(msg)
            return False
        
        elif word == "REQUESTKEYVALUES":
            self.sendKeyValues(msg)
            return True
        
        else:
            return False
        
    def configGame(self, msg):
        # word == "NEWGAME"
        self.yourName = msg[1]
        self.oppName = msg[2]
        self.stackSize = int(msg[3])
        self.bb = int(msg[4])
        self.numHands = float(msg[5])

        self.command = "" # clear out command variable

    def configHand(self, msg):
        # word == "NEWHAND"

        self.handID = int(msg[1])
        self.button = msg[2]=="true"
        self.hand3 = [msg[3], msg[4], msg[5]]
        self.yourBank = int(msg[6])
        self.oppBank = int(msg[7])
        self.timeBank = float(msg[8])
        
        self.numBoardCards = 0
        self.boardCards = []

        self.yourBankH.append( [ int(msg[6]) ] )
        self.oppBankH.append( [ int(msg[7]) ] )
                
        self.command = ""  # clear out command variable
        pass

    def storeKey(self, msg):
        # word == "KEYVALUE"
        # TODO maybe
        pass
    
    def sendKeyValues(self, msg):
        # word == "REQUESTKEYVALUES"
        # TODO maybe
        self.command = "FINISH"
        pass
    
    def getAction(self, msg):
        # word = "GETACTION"
        self.potSizes.append(int(msg[1]))
        self.numBoardCards = int(msg[2])
        self.timeBank = float(msg[-1])
        
        boardCardsIndex = 3 #beginning of [boardCards]
        self.boardCards = msg[boardCardsIndex : boardCardsIndex + self.numBoardCards]
        
        numLastActionsIndex = boardCardsIndex + self.numBoardCards
        lastActionsIndex = numLastActionsIndex + 1
        numLastActions = int(msg[numLastActionsIndex])
        
        lastActions = msg[lastActionsIndex : lastActionsIndex + numLastActions]
        
        numLegalActionsIndex = lastActionsIndex + numLastActions
        legalActionsIndex = numLegalActionsIndex + 1
        numLegalActions = int(msg[numLegalActionsIndex])
        
        legalActions = msg[legalActionsIndex : legalActionsIndex + numLegalActions]
        
        
        legalActionsDict = {}
        for x in legalActions:
            legalAct = x.split(":")
            if len(legalAct) > 1:
                legalActionsDict[legalAct[0]] = (int(legalAct[1]), int(legalAct[2]))
            else:
                legalActionsDict[legalAct[0]] = True
                
        print legalActionsDict
        
            
        for x in lastActions:
            self.pastActions.append(x)
            if "DEAL" in x:
                self.yourPastActions.append(x)
                self.oppPastActions.append(x)
            elif self.oppName in x:
                parsedX = x.split(":")
                self.oppPastActions.append(parsedX[0:-1])
            elif self.yourName in x:
                parsedX = x.split(":")
                self.yourPastActions.append(parsedX[0:-1])
                
        print self.yourPastActions
        print self.oppPastActions
                
                
            
            
            
        
        
        
        numBoardCards = self.numBoardCards
        if numBoardCards == 0:
            self.getPreflopAction(legalActionsDict)
        elif numBoardCards == 3:
            self.getFlopAction(legalActionsDict)
        elif numBoardCards == 4:
            self.hand2EQ=EQcalc("".join(self.hand2)+":xx","".join(self.boardCards),self.discardCard,800).ev[0]
            self.getTurnAction(legalActionsDict)
        elif numBoardCards == 5:
            self.hand2EQ=EQcalc("".join(self.hand2)+":xx","".join(self.boardCards),self.discardCard,800).ev[0]
            self.getRiverAction(legalActionsDict)
            
        
        
    def handOver(self, msg):
        # word == "HANDOVER"
        
        boardCardsIndex = 4 #beginning of [boardCards]
        
        numLastActionsIndex = boardCardsIndex + int(msg[3])
        lastActionsIndex = numLastActionsIndex + 1
        numLastActions = int(msg[numLastActionsIndex])
        
        lastActions = msg[lastActionsIndex : lastActionsIndex + numLastActions]
        
        for x in lastActions:
            self.pastActions.append(x)
            if "DEAL" in x:
                self.yourPastActions.append(x)
                self.oppPastActions.append(x)
            elif self.oppName in x:
                parsedX = x.split(":")
                self.oppPastActions.append(parsedX[0:-1])
            elif self.yourName in x:
                parsedX = x.split(":")
                self.yourPastActions.append(parsedX[0:-1])
        
        
        print self.yourPastActions
        print self.oppPastActions
        
        self.timeBank = float(msg[-1])
        self.yourPastActionsH.append(self.yourPastActions)
        self.oppPastActionsH.append(self.oppPastActions)
        self.pastActionsH.append(self.pastActions)
        
        #update player history:
        self.oppActAfterPreflopAction()
        self.oppPreflopRaise()
        self.count()
        
        print "@@@@@@@@@@@@"
        print self.checkAfterPreflopCall
        print self.raiseAfterPreflopCall
        print self.oppAveragePreflopRaise
        print self.foldAfterPreflopRaise
        print self.callAfterPreflopRaise
        print self.raiseAfterPreflopRaise
        
        
        #reset variables
        self.hand3 = []
        self.hand2 = []
        self.yourBank = int(msg[1])
        self.oppBank = int(msg[2])
        self.potSizesH.append(self.potSizes)
        self.potSizes = []
        self.numBoardCards = 0
        self.boardCards = []
        self.discardCard = ""
        self.hand2EQ = 0 
        
     
        
        self.yourPastActions = []
        self.oppPastActions = []
        self.pastActions = []
        
 
        
        self.command = ""
        #TODO
            
    def getPreflopAction(self, legalActionsDict):
        Score = preflop.pointvalue(self.hand3)[-1]
        if "RAISE" in legalActionsDict:
            minRaise = legalActionsDict["RAISE"][0]
            maxRaise = legalActionsDict["RAISE"][1]
        potsize = self.potSizes[-1]
        buttonRaiseFold = 0
        buttonRaiseCall = 0.5
        buttonRaiseRaise = 0.5
        buttonCallCheck = 0.5
        buttonCallRaise = 0.5
        bigFold = 0.5
        bigCall = 0.5
        bigRaise = 0.5
        bigCallRaiseFold = 0
        bigCallRaiseCall = 0.5
        bigCallRaiseRaise = 0.5
        bigRaiseRaiseRaise = 0.5
        
        if self.button == True and potsize == 3:
            Mean = Score/4 + 1
            Std = 0
            RandomNumber = random.normalvariate(Mean, Std)
            if RandomNumber <= 1:
                RandomNumber = 1
            if Mean >= 5:
                Probability = random.uniform(0, 1)
                if Probability > buttonRaiseFold:
                    self.command = "RAISE:" + str(minRaise)
                else:
                    self.command = "CALL"
            elif Mean >= 4.5:
                Probability = random.uniform(0, 1)
                if Probability < buttonRaiseFold:  #Raise more when they have higher chance of folding
                    RaiseAmount = min(int((RandomNumber+2)*minRaise), maxRaise)
                    self.command = "RAISE:" + str(RaiseAmount)
                else:
                    Probability2 = random.uniform(0, 1) #for buttonCallRaise
                    if Probability2 < buttonCallRaise:  #if we call they are going to raise us anyways, so we might as well raise
                        RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                        self.command = "RAISE:" + str(RaiseAmount)
                    else:
                        self.command = "CALL"
            elif Mean >= 3.5:
                Probability = random.uniform(0, 1) + 0.1 #for buttonRaiseFold
                if buttonRaiseFold > 0.8:
                    RaiseAmount = min((RandomNumber + 2)*minRaise, maxRaise)
                    self.command = "RAISE:" + str(RaiseAmount)
                elif Probability < buttonRaiseFold: #Raise more when they have higher chance of folding
                    Probability2 = random.uniform(0, 1) #for buttonRaiseRaise
                    if Probability2 > buttonRaiseRaise: #only want to Raise when you are not going to get re-raised
                        RaiseAmount = min(int((RandomNumber + 1)*minRaise), maxRaise)
                        self.command = "RAISE:" + str(RaiseAmount)
                    else:
                        Probability3 = random.uniform(0, 1) #for buttonCallRaise
                        if Probability3 < buttonCallRaise: #if we call they are going to raise us anyways, so we might as well raise
                            RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                            self.command = "RAISE:" + str(RaiseAmount)
                        else:
                            self.command = "CALL"
                else:
                    if buttonRaiseFold > 0.5:
                        RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                        self.command = "RAISE:" + str(RaiseAmount)
                    elif buttonRaiseCall > 0.5:
                        self.command = "RAISE:" + str(minRaise)
                    else:
                        self.command = "CALL"
            else:
                Probability = random.uniform(0, 1) + 0.2 #for buttonRaiseFold
                if buttonRaiseFold > 0.8:
                    RaiseAmount = min((RandomNumber+2)*minRaise, maxRaise)
                    self.command = "RAISE:" + str(RaiseAmount)
                elif Probability < buttonRaiseFold: #Raise more when they have higher chance of folding
                    Probability2 = random.uniform(0, 1) - 0.1 #for buttonRaiseRaise
                    if Probability2 > buttonRaiseRaise: #only want to Raise when you are not going to get re-raised
                        RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                        self.command = "RAISE:" + str(RaiseAmount)
                    else:
                        self.command = "FOLD"
                else:
                    Probability3 = random.uniform(0, 1) #for buttonCallCheck
                    if Probability3 < buttonCallCheck:  #would want to call if he will check
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
        elif self.button == True:
            Mean = Score/4 + 1
            Std = 0
            RandomNumber = random.normalvariate(Mean, Std)

            oppLastActionBet = self.totalOppContribution()
            yourLastActionBet = self.totalYourContribution()
    
    
    
            oppLastAction = self.oppPastActions[-1][0]
            yourLastAction = self.yourPastActions[-1][0]
            potOdds = (oppLastActionBet-yourLastActionBet)/(2*oppLastActionBet)
            normPotOdds = potOdds/0.6
            if Score/20 >= normPotOdds*1.25 and Score >= 13:
                if "RAISE" in legalActionsDict:
                    RaiseAmount = min(int((RandomNumber+2)*minRaise), maxRaise)
                    self.command = "RAISE:" + str(RaiseAmount)
                else:
                    self.command = "CALL"
            else:
                Probability = random.uniform(0, 1)
                if (Probability < buttonCallRaise or buttonCallRaise > 0.8) and yourLastAction == "CALL": #you called and he is more willing to raise when you call
                    if Score/20 >= normPotOdds and Score >= 11.5:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(minRaise)
                        else:
                            self.command = "CALL"
                    elif (Score/20 >= normPotOdds*0.65 or Score >= 10.5) and Score >= 8.5:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                elif (Probability < buttonRaiseRaise or buttonRaiseRaise > 0.8) and yourLastAction != "CALL":
                    if Score/20 >= normPotOdds*1.1 and Score >= 12:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(minRaise)
                        else:
                            self.command = "CALL"
                    if (Score/20 >= normPotOdds*0.8 or Score >= 10.5) and Score >= 9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                else:
                    if Score/20 >= normPotOdds*1.15 and Score >= 12:
                        if "RAISE" in legalActionsDict:
                            RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                            self.command = "RAISE:" + str(RaiseAmount)
                        else:
                            self.command = "CALL"
                    if (Score/20 >= normPotOdds*0.9 or Score >= 11) and Score >= 9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"   
        else: #self.button == False:
            Mean = Score/4 + 1
            Std = 0
            RandomNumber = random.normalvariate(Mean, Std)
            oppLastActionBet = self.totalOppContribution()
            yourLastActionBet = self.totalYourContribution()
    
    
    
            oppLastAction = self.oppPastActions[-1][0]
            yourLastAction = self.yourPastActions[-1][0]
            potOdds = (oppLastActionBet-yourLastActionBet)/(2*oppLastActionBet)
            normPotOdds = potOdds/0.6
            
            if oppLastAction == "RAISE" and yourLastAction != "RAISE":
                Probability = random.uniform(0, 1) - 0.1
                if bigRaise < 0.5 and (bigRaise < 0.2 or Probability > bigRaise):
                    if Score/20 >= normPotOdds*1.25 and Score >= 12.5:
                        self.command = "CALL"
                    elif (Score/20 >= normPotOdds*0.9 or Score >= 11) and Score >= 9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD" 
                else:
                    if Score/20 >= normPotOdds and Score >= 12:
                        self.command = "CALL"
                    elif (Score/20 >= normPotOdds*0.7 or Score >= 10.5) and Score >= 9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD" 
            elif oppLastAction == "RAISE":  #if they raised your raise
                Probability = random.uniform(0, 1) - 0.1
                if bigRaiseRaiseRaise > 0.8:
                    if Score/20 >= normPotOdds and Score >= 11.5:
                        self.command = "CALL"
                    elif (Score/20 >= normPotOdds*0.7 or Score >= 10.5) and Score >= 9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"  
                if bigRaiseRaiseRaise < 0.5 and (bigRaiseRaiseRaise < 0.2 or Probability > bigRaiseRaiseRaise):
                    if Score/20 >= normPotOdds*1.25 and Score >= 13:
                        self.command = "CALL"
                    elif (Score/20 >= normPotOdds or Score >= 11) and Score >= 10:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD" 
                else:
                    if Score/20 >= normPotOdds and Score >= 13.5:
                        self.command = "CALL"
                    elif (Score/20 >= normPotOdds*0.8 or Score >= 11) and Score >= 9.5:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
            else: #they just called
                Mean = Score/4 + 1
                Std = 0
                RandomNumber = random.normalvariate(Mean, Std)
                if RandomNumber <= 1:
                    RandomNumber = 1
                if Mean >= 4.5:
                    Probability = random.uniform(0, 1)
                    if Probability > bigCallRaiseFold:
                        self.command = "RAISE:" + str(minRaise)
                    else:
                        self.command = "CHECK"
                elif Mean >= 4.25:
                    Probability = random.uniform(0, 1)
                    if Probability < bigCallRaiseFold:  #Raise more when they have higher chance of folding
                        RaiseAmount = min(int((RandomNumber+2)*minRaise), maxRaise)
                        self.command = "RAISE:" + str(RaiseAmount)
                    else:
                        Probability2 = random.uniform(0, 1) #for bigCallRaiseFold
                        if Probability2 < bigCallRaiseFold:  #if we call they are going to raise us anyways, so we might as well raise
                            RaiseAmount = min(int(RandomNumber*minRaise), maxRaise)
                            self.command = "RAISE:" + str(RaiseAmount)
                        else:
                            self.command = "CHECK"
                elif Mean >= 3.25:
                    self.command = "CHECK"
                else:
                    self.command = "CHECK"

            
    
    def getFlopAction(self, legalActionsDict):
        button=self.button
        # Parse getActionInfo here:
        
        if "DISCARD" in legalActionsDict:
            self.discard()
            self.command = "DISCARD:"+self.discardCard
        else:
            self.discard() #calculate EQ
            if "BET" in legalActionsDict:
                minBet = legalActionsDict["BET"][0]
                maxBet = legalActionsDict["BET"][1]
            if "RAISE" in legalActionsDict:
                minRaise = legalActionsDict["RAISE"][0]
                maxRaise = legalActionsDict["RAISE"][1]
                
            potsize = self.potSizes[-1]
            
            firstBetFold = 0.5
            firstBetCall = 0.5
            firstBetRaise = 0.5
            firstCheckCheck = 0.5
            firstCheckRaise = 0.5
            secondCheck = 0.5
            secondRaise = 0.5
            secondCheckRaiseFold = 0.5
            secondCheckRaiseCall = 0.5
            secondCheckRaiseRaise = 0.5
            secondRaiseRaiseRaise = 0.5

            oppLastActionBet = self.totalOppContribution()
            yourLastActionBet = self.totalYourContribution()



            oppLastAction = self.oppPastActions[-1][0]
            yourLastAction = self.yourPastActions[-1][0]
            
            potOdds = (oppLastActionBet-yourLastActionBet)/(2*oppLastActionBet)
            normPotOdds = potOdds/0.5
                    
            
            eq = self.hand2EQ
            Probability = random.uniform(0, 1)
            if self.handID < 30:
                if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                    if eq > 0.8:
                        BetAmount = min(2*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.6 and firstBetFold > 0.8:
                        BetAmount = max(4*minBet, 0.25*potsize)
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.65:
                        BetAmount = min(3*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.55 and firstBetFold > 0.8:
                        BetAmount = minBet
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                elif button == False: #small blind but reacting
                    if yourLastAction == "CHECK":   
                        if eq > normPotOdds and eq > 0.4:
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                    elif yourLastAction == "RAISE" or yourLastAction == "BET":
                        if eq > 0.8:
                            self.command = "CALL"
                        elif eq > 0.6 and eq + 0.1 > normPotOdds:
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                    else:
                        self.command = "FOLD"
                else:  #button is True
                    if oppLastAction == "CHECK":
                        if eq > 0.75:
                            BetAmount = min(2*minBet, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.6 and secondCheckRaiseFold > 0.7:
                            BetAmount = max(4*minBet, 0.25*potsize)
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.6:
                            BetAmount = min(3*minBet, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.5:
                            BetAmount = minBet
                            self.command = "BET:" + str(BetAmount)
                        else:
                            self.command = "CHECK"
                    else: #if opponent bets or raises
                        if eq > 0.85:
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(minRaise)
                            else:
                                self.command = "CALL"
                        elif eq > 0.7 and eq + 0.2 > normPotOdds:
                            self.command = "CALL"
                        elif eq > 0.6 and eq + 0.1 > normPotOdds:
                            self.command = "CALL"
                        elif eq > 0.5 and eq > normPotOdds:
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
            else:
                oppHandsFlop = 0.6  ####################################
                handStrength = (eq - (1-oppHandsFlop))/(oppHandsFlop)
                if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                    if handStrength > 0.8 or eq > 0.9:
                        self.command = "CHECK"
                    elif handStrength > 0.7:
                        Probability = random.uniform(0, 1)
                        if Probability < 0.5:
                            BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        else:
                            self.command = "CHECK"
                    elif eq > 0.8 and handStrength > 0.6:
                        BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif handStrength > 0.6:
                        BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.65 and handStrength > 0.4:
                        BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif firstBetFold > 0.7 and eq > 0.65:
                        BetAmount = int(max(3*maxBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.65:
                        BetAmount = int(max(2*maxBet, 0.15*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                elif button == False: #small blind but reacting
                    if yourLastAction == "CHECK":
                        if handStrength > 0.8 or eq > 0.9:
                            if "RAISE" in legalActionsDict:
                                Raise = int((4+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif handStrength > 0.7:
                            if "RAISE" in legalActionsDict:
                                Raise = int((3+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif eq > 0.75 and eq > normPotOdds:
                            self.command = "CALL"
                        elif (eq > 0.65 or handStrength > 0.5) and handStrength > normPotOdds and eq > 0.4:
                            self.command = "CALL"
                        elif firstCheckRaise > 0.5 and eq > 0.55 and handStrength > normPotOdds:
                            self.command = "CALL"
                        elif eq > 0.51 and eq > normPotOdds + 0.1:
                            self.command = "CALL"
                        elif eq > 0.44 and handStrength > 0.25 and betCheckRaise > 0.5 and eq > (normPotOdds + 0.1):
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                    elif yourLastAction == "RAISE" or yourLastAction == "BET":
                        Probability = random.uniform(0, 1)
                        if eq > 0.85 and firstBetRaise > 0.4:
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(maxRaise)
                            else:
                                self.command = "CALL"
                        elif handStrength > 0.7 or eq > 0.85:
                            if "RAISE" in legalActionsDict:
                                Raise = int((3+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif eq > 0.8 and handStrength > 0.6:
                            if "RAISE" in legalActionsDict:
                                Raise = int((2+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif handStrength > 0.6:
                            Probability = random.uniform(0, 1)
                            if (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/5)):
                                if "RAISE" in legalActionsDict:
                                    self.command = "RAISE:" + str(minRaise)
                                else:
                                    self.command = "CALL"
                            else:
                                self.command = "CALL"
                        elif eq > 0.65 and handStrength > 0.4 and (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/9)):
                                self.command = "CALL"
                        elif eq > 0.65:
                            if eq > (normPotOdds - firstBetRaise/12):
                                self.command = "CALL"
                            else:
                                self.command = "FOLD"
                        else:
                            self.command = "FOLD"
                    else:
                        self.command = "FOLD"
                else: #if button = True
                    if oppLastAction == "CHECK":
                        if handStrength > 0.8 or eq > 0.9:
                            self.command = "CHECK"
                        elif handStrength > 0.65:
                            Probability = random.uniform(0, 1)
                            if Probability < 0.5:
                                BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                                self.command = "BET:" + str(BetAmount)
                            else:
                                self.command = "CHECK"
                        elif eq > 0.75 and handStrength > 0.55:
                            BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif handStrength > 0.55:
                            BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.65 and handStrength > 0.35:
                            BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif secondCheckRaiseFold > 0.7 and eq > 0.65:
                            BetAmount = int(max(3*maxBet, 0.25*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.6:
                            BetAmount = int(max(2*maxBet, 0.15*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        elif eq > 0.5 and secondCheckRaiseFold > 0.65:
                            BetAmount = int(max(2*maxBet, 0.15*potsize))
                            BetAmount = min(BetAmount, maxBet)
                            self.command = "BET:" + str(BetAmount)
                        else:
                            self.command = "CHECK"
                    elif oppLastAction == "BET" or oppLastAction == "RAISE":
                        if eq > 0.83 and secondRaise > 0.6:
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(maxRaise)
                            else:
                                self.command = "CALL"
                        elif handStrength > 0.7 or eq > 0.85:
                            
                            if "RAISE" in legalActionsDict:
                                Raise = int((3+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif eq > 0.78 and handStrength > 0.6:
                            if "RAISE" in legalActionsDict:
                                Raise = int((2+handStrength)*minRaise)
                                Raise = min(Raise, maxRaise)
                                self.command = "RAISE:" + str(Raise)
                            else:
                                self.command = "CALL"
                        elif handStrength > 0.6:
                            Probability = random.uniform(0, 1)
                            if (Probability < secondRaise or secondRaise > 0.8) and (eq > normPotOdds - secondRaise/5):
                                if "RAISE" in legalActionsDict:
                                    self.command = "RAISE:" + str(minRaise)
                                else:
                                    self.command = "CALL"
                            else:
                                self.command = "CALL"
                        elif eq > 0.63 and handStrength > 0.4 and (Probability < secondRaise or secondRaise > 0.8) and (eq > (normPotOdds - secondRaise/9)):
                            self.command = "CALL"
                        elif eq > 0.63 and eq > (normPotOdds - secondRaise/12):
                            self.command = "CALL"
                        elif eq > 0.58 and eq > (normPotOdds - secondRaise/20):
                            self.command = "CALL"
                        elif eq > 0.52 and eq > normPotOdds + 0.1:
                            self.command = "CALL"
                        elif eq > 0.44 and eq > normPotOdds + 0.1 and secondRaise > 0.8:
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                     
                        
                        
                    
        
            
    

    

            #INSERT
        
            
            
        
        
        
        #TODO
        
    
    def getTurnAction(self, legalActionsDict):
        button = self.button

        if "BET" in legalActionsDict:
            minBet = legalActionsDict["BET"][0]
            maxBet = legalActionsDict["BET"][1]
        if "RAISE" in legalActionsDict:
            minRaise = legalActionsDict["RAISE"][0]
            maxRaise = legalActionsDict["RAISE"][1]
            
        potsize = self.potSizes[-1]
        
        firstBetFold = 0.5
        firstBetCall = 0.5
        firstBetRaise = 0.5
        firstCheckCheck = 0.5
        firstCheckRaise = 0.5
        secondCheck = 0.5
        secondRaise = 0.5
        secondCheckRaiseFold = 0.5
        secondCheckRaiseCall = 0.5
        secondCheckRaiseRaise = 0.5
        secondRaiseRaiseRaise = 0.5

        oppLastActionBet = self.totalOppContribution()
        yourLastActionBet = self.totalYourContribution()



        oppLastAction = self.oppPastActions[-1][0]
        yourLastAction = self.yourPastActions[-1][0]
        
        potOdds = (oppLastActionBet-yourLastActionBet)/(2*oppLastActionBet)
        normPotOdds = potOdds/0.5
 
            
        
        eq = self.hand2EQ
        Probability = random.uniform(0, 1)
        if self.handID < 30:
            if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                if eq > 0.87:
                    BetAmount = min(2*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.74 and firstBetFold > 0.8:
                    BetAmount = max(4*minBet, 0.25*potsize)
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.74:
                    BetAmount = min(3*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.69 and firstBetFold > 0.8:
                    BetAmount = minBet
                    self.command = "BET:" + str(BetAmount)
                else:
                    self.command = "CHECK"
            elif button == False: #small blind but reacting
                if yourLastAction == "CHECK":
                    if eq > normPotOdds and eq > 0.6:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                elif yourLastAction == "RAISE" or yourLastAction == "BET":
                    if eq > 0.86:
                        self.command = "CALL"
                    elif eq > 0.72 and eq + 0.1 > normPotOdds:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                else:
                    self.command = "FOLD"
            else:  #button is True
                if oppLastAction == "CHECK":
                    if eq > 0.82:
                        BetAmount = min(2*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.68 and secondCheckRaiseFold > 0.77:
                        BetAmount = max(4*minBet, 0.25*potsize)
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.68:
                        BetAmount = min(3*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.58:
                        BetAmount = minBet
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                else: #if opponent bets or raises
                    if eq > 0.92:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(minRaise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.76 and eq + 0.12 > normPotOdds:
                        self.command = "CALL"
                    elif eq > 0.67 and eq + 0.05 > normPotOdds:
                        self.command = "CALL"
                    elif eq > 0.57 and eq > normPotOdds:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
        else:
            oppHandsFlop = 0.5  ####################################
            handStrength = (eq - (1-oppHandsFlop))/(oppHandsFlop)
            if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                if handStrength > 0.83 or eq > 0.98:
                    self.command = "CHECK"
                elif handStrength > 0.74:
                    BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.86 and handStrength > 0.64:
                    BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif handStrength > 0.66:
                    BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.72 and handStrength > 0.4:
                    BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif firstBetFold > 0.7 and eq > 0.72:
                    BetAmount = int(max(3*maxBet, 0.25*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.72:
                    BetAmount = int(max(2*maxBet, 0.15*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                else:
                    self.command = "CHECK"
            elif button == False: #small blind but reacting
                Probability = random.uniform(0, 1)
                if yourLastAction == "CHECK":
                    if handStrength > 0.8 or eq > 0.9:
                        if "RAISE" in legalActionsDict:
                            Raise = int((4+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.72:
                        if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.81 and eq > normPotOdds:
                        self.command = "CALL"
                    elif (eq > 0.74 or handStrength > 0.5) and handStrength > normPotOdds and eq > 0.5:
                        self.command = "CALL"
                    elif firstCheckRaise > 0.5 and eq > 0.64 and handStrength > normPotOdds:
                        self.command = "CALL"
                    elif eq > 0.6 and eq > normPotOdds + 0.1:
                        self.command = "CALL"
                    elif eq > 0.52 and handStrength > 0.3 and betCheckRaise > 0.5 and eq > (normPotOdds + 0.1):
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                elif yourLastAction == "RAISE" or yourLastAction == "BET":
                    if eq > 0.9 and firstBetRaise > 0.4:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(maxRaise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.7 or eq > 0.85:
                        
                        if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.8 and handStrength > 0.6:
                        
                        if "RAISE" in legalActionsDict:
                            Raise = int((2+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.6:
                        Probability = random.uniform(0, 1)
                        if (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/5)):
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(minRaise)
                            else:
                                self.command = "CALL"
                        else:
                            self.command = "CALL"
                    elif eq > 0.67 and handStrength > 0.4 and (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/9)):
                            self.command = "CALL"
                    elif eq > 0.67:
                        if eq > (normPotOdds - firstBetRaise/12):
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                    else:
                        self.command = "FOLD"
                else:
                    self.command = "FOLD"
            else: #if button = True
                if oppLastAction == "CHECK":
                    if handStrength > 0.8 or eq > 0.9:
                        BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif handStrength > 0.65:
                        BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.81 and handStrength > 0.6:
                        BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif handStrength > 0.6:
                        BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.71 and handStrength > 0.35:
                        BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif secondCheckRaiseFold > 0.7 and eq > 0.71:
                        BetAmount = int(max(3*maxBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.68:
                        BetAmount = int(max(2*maxBet, 0.15*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.58 and secondCheckRaiseFold > 0.65:
                        BetAmount = int(max(2*maxBet, 0.15*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                elif oppLastAction == "BET" or oppLastAction == "RAISE":
                    Probability = random.uniform(0, 1)
                    if eq > 0.96 and secondRaise > 0.6:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(maxRaise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.7 or eq > 0.92:
                        
                        if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.83 and handStrength > 0.63:
                        
                        if "RAISE" in legalActionsDict:
                            Raise = int((2+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.63:
                        Probability = random.uniform(0, 1)
                        if (Probability < secondRaise or secondRaise > 0.8) and (eq > normPotOdds - secondRaise/5):
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(minRaise)
                            else:
                                self.command = "CALL"
                        else:
                            self.command = "CALL"
                    elif eq > 0.7 and handStrength > 0.4 and (Probability < secondRaise or secondRaise > 0.8) and (eq > (normPotOdds - secondRaise/9)):
                        self.command = "CALL"
                    elif eq > 0.7 and eq > (normPotOdds - secondRaise/12):
                        self.command = "CALL"
                    elif eq > 0.65 and eq > (normPotOdds - secondRaise/20):
                        self.command = "CALL"
                    elif eq > 0.59 and eq > normPotOdds + 0.1:
                        self.command = "CALL"
                    elif eq > 0.5 and eq > normPotOdds + 0.1 and secondRaise > 0.8:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"

    def getRiverAction(self, legalActionsDict):
        button = self.button

        if "BET" in legalActionsDict:
            minBet = legalActionsDict["BET"][0]
            maxBet = legalActionsDict["BET"][1]
        if "RAISE" in legalActionsDict:
            minRaise = legalActionsDict["RAISE"][0]
            maxRaise = legalActionsDict["RAISE"][1]
            

        potsize = self.potSizes[-1]
        
        firstBetFold = 0.5
        firstBetCall = 0.5
        firstBetRaise = 0.5
        firstCheckCheck = 0.5
        firstCheckRaise = 0.5
        secondCheck = 0.5
        secondRaise = 0.5
        secondCheckRaiseFold = 0.5
        secondCheckRaiseCall = 0.5
        secondCheckRaiseRaise = 0.5
        secondRaiseRaiseRaise = 0.5

        oppLastActionBet = self.totalOppContribution()
        yourLastActionBet = self.totalYourContribution()



        oppLastAction = self.oppPastActions[-1][0]
        yourLastAction = self.yourPastActions[-1][0]
        
        potOdds = (oppLastActionBet-yourLastActionBet)/(2*oppLastActionBet)
        normPotOdds = potOdds/0.5
        
        eq = self.hand2EQ
        Probability = random.uniform(0, 1)
        if self.handID < 30:
            if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                if eq > 0.93:
                    BetAmount = min(2*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.84 and firstBetFold > 0.6:
                    BetAmount = max(4*minBet, 0.25*potsize)
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.84:
                    BetAmount = min(3*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.8 and firstBetFold > 0.6:
                    BetAmount = minBet
                    self.command = "BET:" + str(BetAmount)
                else:
                    self.command = "CHECK"
            elif button == False: #small blind but reacting
                if yourLastAction == "CHECK":
                    if eq > normPotOdds and eq > 0.9:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                elif yourLastAction == "RAISE" or yourLastAction == "BET":
                    if eq > 0.93:
                        self.command = "CALL"
                    elif eq > 0.8 and eq + 0.05 > normPotOdds:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                else:
                    self.command = "FOLD"
            else:  #button is True
                if oppLastAction == "CHECK":
                    if eq > 0.93:
                        BetAmount = min(5*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.8 and secondCheckRaiseFold > 0.6:
                        BetAmount = max(4*minBet, 0.25*potsize)
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.8:
                        BetAmount = min(3*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.73:
                        BetAmount = minBet
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                else: #if opponent bets or raises
                    if eq > 0.96:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(10*minRaise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.75 and eq > normPotOdds:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
        else:
            oppHandsFlop = 0.3  ####################################
            handStrength = (eq - (1-oppHandsFlop))/(oppHandsFlop)
            if button == False and "BET" in legalActionsDict: #you are acting first (no re-raises)
                if handStrength > 0.8 or eq > 0.95:
                    self.command = "BET:" + str(15*minBet)
                elif handStrength > 0.74:
                    BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.86 and handStrength > 0.68:
                    BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif handStrength > 0.68:
                    BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.78 and handStrength > 0.4:
                    BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif firstBetFold > 0.7 and eq > 0.78:
                    BetAmount = int(max(3*maxBet, 0.25*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                elif eq > 0.78:
                    BetAmount = int(max(2*maxBet, 0.15*potsize))
                    BetAmount = min(BetAmount, maxBet)
                    self.command = "BET:" + str(BetAmount)
                else:
                    self.command = "CHECK"
            elif button == False: #small blind but reacting
                Probability = random.uniform(0, 1)
                if yourLastAction == "CHECK":
                    if handStrength > 0.82 or eq > 0.95:
                        if "RAISE" in legalActionsDict:
                            Raise = int((4+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.76:
                         if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                         else:
                            self.command = "CALL"
                    elif eq > 0.84 and eq > normPotOdds:
                        self.command = "CALL"
                    elif (eq > 0.78 or handStrength > 0.5) and handStrength > normPotOdds and eq > 0.7:
                        self.command = "CALL"
                    elif firstCheckRaise > 0.5 and eq > 0.73 and handStrength > normPotOdds:
                        self.command = "CALL"
                    elif eq > 0.73 and eq > normPotOdds + 0.1:
                        self.command = "CALL"
                    elif eq > 0.68 and handStrength > 0.3 and betCheckRaise > 0.5 and eq > (normPotOdds + 0.1):
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                elif yourLastAction == "RAISE" or yourLastAction == "BET":
                    if eq > 0.96 and firstBetRaise > 0.4:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(maxRaise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.75 or eq > 0.94:
                        if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.91 and handStrength > 0.71:
                        if "RAISE" in legalActionsDict:
                            Raise = int((2+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.71:
                        Probability = random.uniform(0, 1)
                        if (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/5)):
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(minRaise)
                            else:
                                self.command = "CALL"
                        else:
                            self.command = "CALL"
                    elif eq > 0.7 and handStrength > 0.45 and (Probability < firstBetRaise or firstBetRaise > 0.8) and (eq > (normPotOdds - firstBetRaise/9)):
                            self.command = "CALL"
                    elif eq > 0.7:
                        if eq > (normPotOdds - firstBetRaise/12):
                            self.command = "CALL"
                        else:
                            self.command = "FOLD"
                    else:
                        self.command = "FOLD"
                else:
                    self.command = "FOLD"
            else: #if button = True
                if oppLastAction == "CHECK":
                    if handStrength > 0.8 or eq > 0.9:
                        BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif handStrength > 0.68:
                        BetAmount = min(10*handStrength*handStrength*minBet, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.82 and handStrength > 0.6:
                        BetAmount = int(max(12*handStrength*eq*minBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif handStrength > 0.61:
                        BetAmount = int(max(10*handStrength*handStrength*minBet, 0.33*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.74 and handStrength > 0.45:
                        BetAmount = int(max(12*handStrength*handStrength*minBet, 0.3*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif secondCheckRaiseFold > 0.7 and eq > 0.71:
                        BetAmount = int(max(3*maxBet, 0.25*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.72:
                        BetAmount = int(max(2*maxBet, 0.15*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    elif eq > 0.64 and secondCheckRaiseFold > 0.6:
                        BetAmount = int(max(2*maxBet, 0.15*potsize))
                        BetAmount = min(BetAmount, maxBet)
                        self.command = "BET:" + str(BetAmount)
                    else:
                        self.command = "CHECK"
                elif oppLastAction == "BET" or oppLastAction == "RAISE":
                    Probability = random.uniform(0, 1)
                    if eq > 0.97 and secondRaise > 0.6:
                        if "RAISE" in legalActionsDict:
                            self.command = "RAISE:" + str(maxRaise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.7 or eq > 0.95:
                        if "RAISE" in legalActionsDict:
                            Raise = int((3+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif eq > 0.88 and handStrength > 0.65:
                        if "RAISE" in legalActionsDict:
                            Raise = int((2+handStrength)*minRaise)
                            Raise = min(Raise, maxRaise)
                            self.command = "RAISE:" + str(Raise)
                        else:
                            self.command = "CALL"
                    elif handStrength > 0.65:
                        Probability = random.uniform(0, 1)
                        if (Probability < secondRaise or secondRaise > 0.7) and (eq > normPotOdds - secondRaise/5):
                            if "RAISE" in legalActionsDict:
                                self.command = "RAISE:" + str(minRaise)
                            else:
                                self.command = "CALL"
                        else:
                            self.command = "CALL"
                    elif eq > 0.76 and handStrength > 0.52 and (Probability < secondRaise or secondRaise > 0.7) and (eq > (normPotOdds - secondRaise/9)):
                        self.command = "CALL"
                    elif eq > 0.76 and eq > (normPotOdds - secondRaise/12):
                        self.command = "CALL"
                    elif eq > 0.72 and eq > (normPotOdds - secondRaise/20):
                        self.command = "CALL"
                    elif eq > 0.68 and eq > normPotOdds + 0.1:
                        self.command = "CALL"
                    elif eq > 0.63 and eq > normPotOdds + 0.1 and secondRaise > 0.8:
                        self.command = "CALL"
                    else:
                        self.command = "FOLD"
                        
    def discard(self):
        hand = self.hand3
        board = "".join(self.boardCards)
        
        eq12 = EQcalc(hand[0]+hand[1]+":xx",board,hand[2],800).ev[0]
        eq23 = EQcalc(hand[1]+hand[2]+":xx",board,hand[0],800).ev[0]
        eq13 = EQcalc(hand[0]+hand[2]+":xx",board,hand[1],800).ev[0]
        
        if eq12 > eq23 and eq12 > eq13:
            #self.command="DISCARD:"+hand[2]
            self.hand2EQ = eq12
            self.hand2 = [hand[0],hand[1]]
            self.discardCard = hand[2]
        elif eq23 > eq13:
            #self.command="DISCARD:"+hand[0]
            self.hand2EQ = eq23
            self.hand2 = [hand[1],hand[2]]
            self.discardCard = hand[0]
        else:
            #self.command="DISCARD:"+hand[1]
            self.hand2EQ = eq13
            self.hand2 = [hand[0],hand[2]]
            self.discardCard = hand[1]
            
        #optimize
            
    def oppActAfterPreflopAction(self):
        #preflop
        if len(self.pastActions)>2:
            if self.button:
                if "CALL" in self.pastActions[2]:
                    self.oppCheckToYourPreflopCallRatio[1]+=1
                    if "CHECK" in self.pastActions[3]:
                        self.oppCheckToYourPreflopCallRatio[0]+=1
                    if self.oppCheckToYourPreflopCallRatio[1] != 0:
                        self.checkAfterPreflopCall = self.oppCheckToYourPreflopCallRatio[0]/self.oppCheckToYourPreflopCallRatio[1]
                        self.raiseAfterPreflopCall = 1 - self.checkAfterPreflopCall
    
                if "RAISE" in self.pastActions[2]:
                    self.buttonRaiseCallRatio[1]+=1
                    self.buttonRaiseFoldRatio[1]+=1
                    self.buttonRaiseRaiseRatio[1]+=1
                    if "FOLD" in self.pastActions[3]:
                        self.buttonRaiseFoldRatio[0]+=1
                        
                    if "CALL" in self.pastActions[3]:
                        self.buttonRaiseCallRatio[0]+=1
                    
                    if "RAISE" in self.pastActions[3]:
                        self.buttonRaiseRaiseRatio[0]+=1
                        
                    self.foldAfterPreflopRaise = self.buttonRaiseFoldRatio[0] / self.buttonRaiseFoldRatio[1]
                    self.callAfterPreflopRaise = self.buttonRaiseCallRatio[0] / self.buttonRaiseCallRatio[1]
                    self.raiseAfterPreflopRaise = self.buttonRaiseRaiseRatio[0] / self.buttonRaiseRaiseRatio[1]
                    
            else:
                self.BBcounter+=1
                if "FOLD" in self.pastActions[2]:
                    self.numFoldAfterBB+=1
                if "CALL" in self.pastActions[2]:
                    self.numCallAfterBB+=1
                    if "RAISE" in self.pastActions[3]:
                        self.BBCRcounter+=1
                        if "FOLD" in self.pastActions[4]:
                            self.numCallRaiseFoldAfterBB+=1
                            
                        if "CALL" in self.pastActions[4]:
                            self.numCallRaiseCallAfterBB+=1
                            
                        if "RAISE" in self.pastActions[4]:
                            self.numCallRaiseRaiseAfterBB+=1
                            
                        self.BBcallRaiseFold = self.numCallRaiseFoldAfterBB/self.BBCRcounter
                        self.BBcallRaiseCall = self.numCallRaiseCallAfterBB/self.BBCRcounter
                        self.BBcallRaiseRaise = self.numCallRaiseRaiseAfterBB/self.BBCRcounter
                if "RAISE" in self.pastActions[2] and "RAISE" in self.pastActions[3]:
                    self.BBRRcounter +=1
                    if "RAISE" in self.pastActions[4]:
                        self.numRaiseRaiseRaiseAfterBB+=1
                        self.BBraiseRaiseRaise=self.numRaiseRaiseRaiseAfterBB/self.BBRRcounter
                    
                
                
        
    
    def oppActAfterPostFlopAction(self):
        pass
        
    
    def count(self):
        if "DEAL:FLOP" in self.pastActions:
            self.numOppFlop += 1
        if "DEAL:TURN" in self.pastActions:
            self.numOppTurn += 1
        if "DEAL:RIVER" in self.pastActions:
            self.numOppRiver += 1
        for x in self.pastActions:
            if "SHOW" in x:
                self.numOppShow += 1
                break
        self.oppFlop = self.numOppFlop/self.handID
        self.oppTurn = self.numOppTurn/self.handID
        self.oppRiver = self.numOppRiver/self.handID
        self.oppShow = self.numOppShow/self.handID
        
                
    def oppPreflopRaise(self):
        placeholder = []
        for x in self.oppPastActions:
            if "RAISE" == x[0]:
                placeholder.append(int(x[1]))
            if "DEAL:FLOP" == x:
                break
        extension = []
        for i in range(len(placeholder)):
            if i == 0:
                extension.append(placeholder[i]-2)
            else:
                extension.append(placeholder[i]-placeholder[i-1])
        self.oppPreflopRaises.extend(extension)
        if len(self.oppPreflopRaises)!=0:
            self.oppAveragePreflopRaise = sum(self.oppPreflopRaises)/len(self.oppPreflopRaises)

    def totalOppContribution(self):
        total = 0
        for x in self.oppPastActions:
            
            if "RAISE" in x or "BET" in x or "POST" in x:
                total += int(x[1])
        return total
    
                
    def totalYourContribution(self):
        total=0
        for x in self.yourPastActions:
            
            if "RAISE" in x or "BET" in x or "POST" in x:
                total += int(x[1])
        return total
            
    

    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.

        print ""
        print "######################"
        print ""
        
        f_in = input_socket.makefile()
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            print data

            sendCommand = self.parse(data) #sends data to other class methods to process and return boolean on whether to send action

            if sendCommand:
                print self.getCommand()
                input_socket.send(self.getCommand()+"\n") #sends string command
                


            ## Formatting .dump
            print ""

            if data.split()[0]=="HANDOVER":
                print ""
                print "######################"
                print ""
            
        # Clean up the socket.
        input_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)
