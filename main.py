import pandas as pd
import time
from functools import wraps

start_all = time.time()

# store each itemset in a list
df = pd.read_csv('groceries.csv', header=None).fillna('')
dataSet = df.values


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f'{time.time() - start}s to do {func.__name__}')
        return result

    return wrapper


# create Candidate 1
@timeit
def create_candidate1(data_set):
    C1 = []
    for transaction in data_set:
        for item in transaction:
            if not [item] in C1:
                C1.append([item])

    C1.sort()
    return list(map(frozenset, C1))


# use frozen set so we can use it as a key in a dict
@timeit
def scanD(D, Ck, minSupport):
    ssCnt = {}
    for tid in D:
        for can in Ck:
            if can.issubset(tid):
                if not can in ssCnt:
                    ssCnt[can] = 1
                else:
                    ssCnt[can] += 1
    numItems = float(len(D))
    retList = []
    supportData = {}
    for key in ssCnt:
        support = ssCnt[key] / numItems
        if support >= minSupport:
            retList.insert(0, key)
        supportData[key] = support
    return retList, supportData


C1 = create_candidate1(dataSet)

# D is a dataset in the setform.
D = list(map(set, dataSet))

# return datasets having support>min-support
L1, suppDat0 = scanD(D, C1, 0.005)


# creates candidate datasets
# creates Ck
@timeit
def aprioriGen(Lk, k):
    retList = []
    lenLk = len(Lk)
    for i in range(lenLk):
        for j in range(i + 1, lenLk):
            L1 = list(Lk[i])[:k - 2]
            L2 = list(Lk[j])[:k - 2]
            L1.sort()
            L2.sort()
            # if first k-2 elements are equal, set union
            if L1 == L2:
                retList.append(Lk[i] | Lk[j])
    return retList


@timeit
def apriori(dataSet, minSupport=0.005):
    C1 = create_candidate1(dataSet)
    D = list(map(set, dataSet))
    L1, supportData = scanD(D, C1, minSupport)
    L = [L1]
    k = 2
    while (len(L[k - 2]) > 0):
        Ck = aprioriGen(L[k - 2], k)
        Lk, supK = scanD(D, Ck, minSupport)  # scan DB to get Lk
        supportData.update(supK)
        L.append(Lk)
        k += 1
    return L, supportData


L, suppData = apriori(dataSet)
aprioriGen(L[0], 2)


@timeit
def calcConf(freqSet, H, supportData, brl, minConf=0.2):
    # create new list to return
    prunedH = []
    for conseq in H:
        # calc confidence
        conf = supportData[freqSet] / supportData[freqSet - conseq]
        if conf >= minConf:
            #print(freqSet - conseq, '-->', conseq, 'conf:', conf)
            brl.append((freqSet - conseq, conseq, conf))
            prunedH.append(conseq)
    return prunedH


@timeit
def rulesFromConseq(freqSet, H, supportData, brl, minConf=0.2):
    m = len(H[0])
    if (len(freqSet) > (m + 1)):  # try further merging
        Hmp1 = aprioriGen(H, m + 1)  # create Hm+1 new candidates
        Hmp1 = calcConf(freqSet, Hmp1, supportData, brl, minConf)
        if (len(Hmp1) > 1):  # need at least two sets to merge
            rulesFromConseq(freqSet, Hmp1, supportData, brl, minConf)


@timeit
def generateRules(L, supportData, minConf=0.2):  # supportData is a dict coming from scanD
    bigRuleList = []
    for i in range(1, len(L)):  # only get the sets with two or more items
        for freqSet in L[i]:
            H1 = [frozenset([item]) for item in freqSet]
            if (i > 1):
                rulesFromConseq(freqSet, H1, supportData, bigRuleList, minConf)
            else:
                calcConf(freqSet, H1, supportData, bigRuleList, minConf)
    return bigRuleList


L, suppData = apriori(dataSet, minSupport=0.005)
rules = generateRules(L, suppData, minConf=0.2)

print(f'{time.time() - start_all}s to do all things!')
