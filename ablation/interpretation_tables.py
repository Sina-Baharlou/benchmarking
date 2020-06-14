# -*- coding: utf-8 -*-

"""Make interpretaion tables

1.) Which interaction model was always among the top 5/top 10-performing configurations for each dataset?
2.) Which loss function was always among the top 5/top 10-performing configuration for each dataset?
3.) Which training assumption was always among the top 5/top 10-performing configurations for each dataset?
4.) Which combination of interaction model and loss function was always among the top 5/top 10-performing configurations for each dataset?
5.) Which combination of interaction models and training assumption was always among the top 5/top 10-performing configurations for each dataset?
6.) Which combination of loss function and training assumption was always among the top 5/top 10-performing configurations for each dataset?
7.) Which combination interaction models, training assumption, loss function was always among the top 5/top 10-performing configurations for each dataset? Did these configurations use inverse triples?
8.) How many of the top 5/top 10 configurations for each dataset use inverse triples?
"""

import os
from collections import Counter
from typing import Iterable, Optional, Union

import click
import pandas as pd
from tabulate import tabulate
from typing.io import TextIO

from collate import SUMMARY_DIRECTORY, read_collation


@click.command()
def main():
    """Make interpretation at top 5, 10, and 15 best."""
    df = read_collation()
    for top in (5, 10, 50):
        with open(os.path.join(SUMMARY_DIRECTORY, f'winners_at_top_{top}.md'), 'w') as file:
            configurations = [
                'model', 'loss', 'training_loop', 'create_inverse_triples',
                ('model', 'loss'), ('model', 'training_loop'), ('loss', 'training_loop'),
                ('model', 'loss', 'training_loop'),
            ]
            for config in configurations:
                print_winners(df=df, top=top, file=file, config=config)


def get_winners_df(
    df: pd.DataFrame,
    top: int,
    config: Union[str, Iterable[str]],
) -> pd.DataFrame:
    if isinstance(config, str):
        config = [config]
    d = {}
    for dataset, sub_df in df.groupby('dataset'):
        top_df = sub_df.sort_values('hits@10', ascending=False).head(top)
        d[dataset] = Counter('_'.join(r) for r in zip(*(top_df[t] for t in config)))
    return pd.DataFrame.from_dict(d).fillna(0).astype(int)


def print_winners(
    df: pd.DataFrame,
    top: int,
    config: Union[str, Iterable[str]],
    file: Optional[TextIO] = None,
) -> None:
    r = get_winners_df(df=df, top=top, config=config)
    title = config if isinstance(config, str) else "-".join(config)
    print(f'## Top {top} Results for `{title}`\n', file=file)
    print(tabulate(r, headers=r.columns, tablefmt='github'), file=file)
    print(file=file)
    _print_winners_helper(r, top, file=file)
    print('', file=file)


def _print_winners_helper(df: pd.DataFrame, top: int, file: Optional[TextIO] = None):
    r_transpose = df.transpose()
    for column in r_transpose.columns:
        if r_transpose[column].all():
            print(f'Winner at N={top}: {column}', file=file)


if __name__ == '__main__':
    main()