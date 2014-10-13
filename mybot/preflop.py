
def pointvalue(hand):
    #takes in list of length 3, each element is string of value followed by suit#
    card = []
    suit = []
    for x in hand:
        card.append(x[0])
        suit.append(x[1])

    orderedHand=[]
    cardOrder = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']

    pairL=[]
    adj=[]
    
    for y in range(13):
        x = cardOrder[y]
        k=0
        for i in range(3):
            if card[i]==x:
                k+=1
                orderedHand.append(hand[i])
                adj.append(y)
        if k!=0:
            pairL.append(k)

        
  

    ocard=[]
    osuit=[]

    for x in orderedHand:
        ocard.append(x[0])
        osuit.append(x[1])

    suitDict={}
    for i in range(3):
        if osuit[i] in suitDict:
            suitDict[osuit[i]][0]+=1
            flushSuit=osuit[i]
        else:
            suitDict[osuit[i]]=[1,i]
    


    

    pts = {'A':10, 'K':8, 'Q':7, 'J':6, 'T':5, '9':4.5, '8':4, '7':3.5,'6':3,'5':2.5,'4':2,'3':1.5, '2':1}

                                
            #HIGH CARD + PAIR or HIGHER chances
            # pair + off: max(double, 5) + value (1/4 if higher, 1/8 if lower).
            # triple = max(double, 5)
            # 3 diff: sum divided by 2
            #BONUS (FLUSH CHANCE)
            #Two cards same suit + third card offsuit:
            #Add max(1/4 the value of the highest same suit card, 1) + 1
            #All three cards same suit:
            #Add 2
            #BONUS (STRAIGHT CHANCE)
            #If two cards are right next to each other + useless third card: +1
            #If two cards are off by 1 card + useless third card: + 0.4
            #If two cards are off by 1 card + other two cards off by 1 card: + 0.6
            #If three cards are right next to each other: + 1.5 (ignore that the two cards are off by 1 card part)
            #If two cards are right next to each other + third card is off by 1 card: +1.2
            #Everything else is negliglble so don't add
            #We can fix the 'AK' and 'A2' things later

    value=0
    ## PAIRS AND TRIPLES
    if len(pairL)==1:
        #triple case
        value+=max(pts[card[1]]*2,5)
        
    elif len(pairL)==2:
        #pair case
        value+=max(pts[orderedHand[1][0]]*2,5)
        if pairL[0]==1:
            value+=pts[orderedHand[0][0]]*.25
            
        else:            
            value+=pts[orderedHand[2][0]]*.125
    else:
        for x in card:
            value+=pts[x]*.5

    ## BONUS (FLUSH CHANCE)

    if len(suitDict)==1:
        #all same suit
        value+=2

    if len(suitDict)==2:
        #2 cards same suit
        value+=max(pts[card[suitDict[flushSuit][1]]]*.25,1)+1

    ## BONUS (STRAIGHT CHANCE)

    if adj[1]-adj[0]==adj[2]-adj[1]==1:
        value+=1.5
    elif adj[1]-adj[0]==1 or adj[2]-adj[1]==1:
        value+=1
    
        
        
    
    return (orderedHand,adj,pairL,value)


numvalue=['A','2','3','4','5','6','7','8','9','T','J','Q','K']
cards = []
for i in ['s','h','c','d']:

    for x in numvalue:
        cards.append(x+i)
print cards
print len(cards)

preflopHands=[]
for x in range(50):
    for y in range(x+1,51):
        for z in range(y+1,52):
            preflopHands.append([cards[x],cards[y],cards[z]])

print preflopHands[-1]
print len(preflopHands)

test = []
#for x in preflopHands:
    #calculate EV
ptdict={'0-5':0,'5-10':0,'5-10':0,'10-15':0,'15-20':0,'20+':0}            
for x in preflopHands:
    val = pointvalue(x)[3]
    test.append(val)
    if val>20:
        ptdict['20+']+=1
    elif val>15:
        ptdict['15-20']+=1
    elif val>10:
        ptdict['10-15']+=1
    elif val>5:
        ptdict['5-10']+=1
    else:
        ptdict['0-5']+=1

print ptdict

test.sort()

print test[len(test)/2]




