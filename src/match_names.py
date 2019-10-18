# File for using random nouns and verbs to generate a chess match name
import random as rand

noun_file = open('assets/nouns.txt', 'r')
nouns = [l for l in noun_file.readlines()]
adjective_file = open('assets/adjectives.txt', 'r')
adjectives = [l for l in adjective_file.readlines()]


def generate_adjective():
    return rand.choice(adjectives)


def generate_noun():
    return rand.choice(nouns)


def generate_match_name():
    """
    Generate a silly name for each chess match that can be used as the email
    subject for the thread. E.g.:
    """
    # TODO would be great if it used the current time as a seed, and even
    # better if the time could be reversed knowing the match name
    adjective = generate_adjective
    noun = generate_noun

    return f'The {adjective()} {noun()} V.S. The {adjective()} {noun()}'
