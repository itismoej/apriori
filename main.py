from collections import namedtuple
from itertools import chain, combinations

import numpy as np
import pandas as pd

from utils import TransactionManager, timeit


def remove_nan_objects(dataframe):
    return np.array(list(map(lambda x: x[~pd.isnull(x)], dataframe.values)), dtype=object)


SupportRecord = namedtuple(
    'SupportRecord', ('items', 'support'))
RelationRecord = namedtuple(
    'RelationRecord', SupportRecord._fields + ('ordered_statistics',))
OrderedStatistic = namedtuple(
    'OrderedStatistic', ('items_base', 'items_add', 'confidence', 'lift',))


def create_next_candidates(prev_candidates, length):
    """
    Returns the apriori candidates as a list.
    Arguments:
        prev_candidates -- Previous candidates as a list.
        length -- The lengths of the next candidates.
    """
    # Solve the items.
    items = sorted(frozenset(chain.from_iterable(prev_candidates)))

    # Create the temporary candidates. These will be filtered below.
    tmp_next_candidates = (frozenset(x) for x in combinations(items, length))

    # Return all the candidates if the length of the next candidates is 2
    # because their subsets are the same as items.
    if length < 3:
        return list(tmp_next_candidates)

    # Filter candidates that all of their subsets are
    # in the previous candidates.
    next_candidates = [
        candidate for candidate in tmp_next_candidates
        if all(
            frozenset(x) in prev_candidates
            for x in combinations(candidate, length - 1))
    ]
    return next_candidates


def gen_support_records(transaction_manager, min_support, **kwargs):
    """
    Returns a generator of support records with given transactions.
    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        min_support -- A minimum support (float).
    Keyword arguments:
        max_length -- The maximum length of relations (integer).
    """
    # Parse arguments.
    max_length = kwargs.get('max_length')

    # For testing.
    _create_next_candidates = kwargs.get(
        '_create_next_candidates', create_next_candidates)

    # Process.
    candidates = transaction_manager.initial_candidates()
    length = 1
    while candidates:
        relations = set()
        for relation_candidate in candidates:
            support = transaction_manager.calc_support(relation_candidate)
            if support < min_support:
                continue
            candidate_set = frozenset(relation_candidate)
            relations.add(candidate_set)
            yield SupportRecord(candidate_set, support)
        length += 1
        if max_length and length > max_length:
            break
        candidates = _create_next_candidates(relations, length)


def gen_ordered_statistics(transaction_manager, record):
    """
    Returns a generator of ordered statistics as OrderedStatistic instances.
    Arguments:
        transaction_manager -- Transactions as a TransactionManager instance.
        record -- A support record as a SupportRecord instance.
    """
    items = record.items
    sorted_items = sorted(items)
    for base_length in range(len(items)):
        for combination_set in combinations(sorted_items, base_length):
            items_base = frozenset(combination_set)
            items_add = frozenset(items.difference(items_base))
            confidence = (
                    record.support / transaction_manager.calc_support(items_base))
            lift = confidence / transaction_manager.calc_support(items_add)
            yield OrderedStatistic(
                frozenset(items_base), frozenset(items_add), confidence, lift)


def filter_ordered_statistics(ordered_statistics, **kwargs):
    """
    Filter OrderedStatistic objects.
    Arguments:
        ordered_statistics -- A OrderedStatistic iterable object.
    Keyword arguments:
        min_confidence -- The minimum confidence of relations (float).
        min_lift -- The minimum lift of relations (float).
    """
    min_confidence = kwargs.get('min_confidence', 0.0)
    min_lift = kwargs.get('min_lift', 0.0)

    for ordered_statistic in ordered_statistics:
        if ordered_statistic.confidence < min_confidence:
            continue
        if ordered_statistic.lift < min_lift:
            continue
        yield ordered_statistic


def apriori(transactions, **kwargs):
    """
    Executes Apriori algorithm and returns a RelationRecord generator.
    Arguments:
        transactions -- A transaction iterable object
                        (eg. [['A', 'B'], ['B', 'C']]).
    Keyword arguments:
        min_support -- The minimum support of relations (float).
        min_confidence -- The minimum confidence of relations (float).
        min_lift -- The minimum lift of relations (float).
        max_length -- The maximum length of the relation (integer).
    """
    # Parse the arguments.
    min_support = kwargs.get('min_support', 0.1)
    min_confidence = kwargs.get('min_confidence', 0.0)
    min_lift = kwargs.get('min_lift', 0.0)
    max_length = kwargs.get('max_length', None)

    # Check arguments.
    if min_support <= 0:
        raise ValueError('minimum support must be > 0')

    # Calculate supports.
    transaction_manager = TransactionManager.create(transactions)
    support_records = gen_support_records(
        transaction_manager, min_support, max_length=max_length)

    # Calculate ordered stats.
    for support_record in support_records:
        ordered_statistics = list(
            filter_ordered_statistics(
                gen_ordered_statistics(transaction_manager, support_record),
                min_confidence=min_confidence,
                min_lift=min_lift,
            )
        )
        if not ordered_statistics:
            continue
        yield RelationRecord(
            support_record.items, support_record.support, ordered_statistics)


def print_rules(rules):
    for item in rules:
        # first index of the inner list
        # Contains base item and add item
        pair = item[0]
        items = [x for x in pair]
        print("Rule: " + items[0] + " -> " + items[1])

        # second index of the inner list
        print("Support: " + str(item[1]))

        # third index of the list located at 0th
        # of the third index of the inner list

        print("Confidence: " + str(item[2][0][2]))
        print("Lift: " + str(item[2][0][3]))
        print("=====================================")


def sort_rules(rules, *, by='lift'):
    if by in ['lift', 'confidence']:
        return sorted(
            rules,
            key=lambda x: getattr(x.ordered_statistics[0], by),
            reverse=True
        )
    elif by == 'confidence':
        return sorted(
            rules,
            key=lambda x: x.support,
            reverse=True
        )
    else:
        raise Exception('invalid value for "by" argument')


@timeit
def run():
    df = pd.read_csv('groceries.csv', header=None)
    data_set = remove_nan_objects(df)
    association_rules = apriori(data_set, min_support=0.005, min_confidence=0.2, min_lift=3)
    rules_sorted_by_lift = sort_rules(association_rules, by='lift')
    print_rules(rules_sorted_by_lift)


if __name__ == '__main__':
    run()
