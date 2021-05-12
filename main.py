import time
from functools import wraps

import numpy as np
import pandas as pd

from apriori import apriori


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f'{time.time() - start}s to {func.__name__}')
        return result

    return wrapper


def remove_nan_objects(dataframe):
    return np.array(list(map(lambda x: x[~pd.isnull(x)], dataframe.values)), dtype=object)


def print_rules(rules):
    for item in rules:
        items = list(item.items)
        print(f"Rule: {items[0]} -> {items[1]}")
        print(f"Support: {item.support:.4f}")
        print(f"Confidence: {item.ordered_statistics[0].confidence:.2f}")
        print(f"Lift: {item.ordered_statistics[0].lift:.2f}")
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
