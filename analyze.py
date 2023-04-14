#!/usr/bin/env python

import argparse
import pstats


def parse_args():
    parser = argparse.ArgumentParser(description='Parse and display profiling results')
    parser.add_argument('-f', '--filename', default='profile.stats', help='path to profile file')
    parser.add_argument('-s', '--sort', choices=['cumulative', 'time', 'calls'], default='cumulative',
                        help='column to sort by')
    parser.add_argument('-n', '--num', type=int, default=50, help='number of results to display')
    return parser.parse_args()


def main():
    args = parse_args()

    stats = pstats.Stats(args.filename)
    sortby = args.sort
    stats.sort_stats(sortby)

    print(f'Top {args.num} results sorted by {sortby}:')
    stats.print_stats(args.num)


if __name__ == '__main__':
    main()
