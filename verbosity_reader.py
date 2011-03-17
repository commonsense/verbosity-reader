from csc.conceptnet4.models import Frame, Frequency, RawAssertion, Language,\
Relation
from events.models import Activity
from django.contrib.auth.models import User
from rhyme import sounds_like_score
from collections import defaultdict
import math, re

make = False

en = Language.get('en')
assertions = []
default = Frequency.objects.get(language=en, text='')
activity, _ = Activity.objects.get_or_create(name='Verbosity')
user = User.objects.get(username='verbosity')

mapping = {
    "it is typically near": 'LocatedNear',
    "it is typically in": 'AtLocation',
    "it is used for": 'UsedFor',
    "it is a kind of": 'IsA',
    "it is a type of": 'IsA',
    "it is related to": 'ConceptuallyRelatedTo',
    "it has": 'HasA',
    "it is": 'HasProperty',
    "it is not": 'IsA',
    "it is about the same size as": 'SimilarSize',
    "it looks like": 'ConceptuallyRelatedTo',
}

bad_regex_no_biscuit =\
  re.compile(r'(^letter|^rhyme|^blank$|^word$|^syllable$|^spell$|^tense$|^prefix|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$|^different|^this$|^that$|^these$|^those$|^mince$)')

maxscore = 0
count = 0
skipcount = 0
counts = defaultdict(int)
text_similarities = []

flag_out = open('flagged_assertions.txt', 'w')
similar_out = open('text_similarity.txt', 'w')
good_out = open('ok_assertions.txt', 'w')
weak_out = open('weak_assertions.txt', 'w')

for line in open('verbosity.txt'):
    if skipcount > 0:
        skipcount -= 1
        continue
    parts = line.strip().split('\t')
    if not parts:
        counts['blank'] += 1
        continue
    left, relation, right, freq, orderscore = parts[:5]

    # catch bad stuff
    flagged = False


    for rword in right.split():
        if bad_regex_no_biscuit.match(rword):
            flagged = True
            break
    if flagged:
        print "FLAGGED:", right
        counts['flag word'] += 1
        flag_out.write(line)
        continue
    if len(right) < 3:
        counts['clue too short'] += 1
        flag_out.write(line)
        continue
    if len(right.split()[-1]) == 1:
        counts['letter'] += 1
        flag_out.write(line)
        continue
    if right.startswith('add') or right.startswith('delete') or right.startswith('remove'):
        counts['flag word'] += 1
        flag_out.write(line)
        continue

    adverb = default
    if right.startswith('not '):
        right = right[4:]
        adverb = Frequency.objects.get(language=en, text='not')
        relation = 'it is not'
    if relation == 'it is the opposite of':
        adverb = Frequency.objects.get(language=en, text='not')
        relation = 'it is not'

    freq = int(freq)
    orderscore = int(orderscore)
    if relation == 'about the same size as':
        relation = 'it is about the same size as'
    elif relation == 'it looks like':
        relation = 'it is related to'
    rel = mapping.get(relation)
    if relation == 'it is' and\
       (right.startswith('a ') or right.startswith('an ')
        or right.startswith('the ')):
        rel = 'IsA'

    if rel is None:
        print "DISCARDED:", relation
        counts['no relation'] += 1
        weak_out.write(line)
        continue
    
    sls = sounds_like_score(left, right)
    text_similarities.append(sls)
    if sls > 0.35:
        print "* %s sounds like %s (%4.4f)" % (left, right, sls)
        counts['text similarity'] += 1
        similar_out.write('%4.4d\t%s' % (sls, line))
        continue
    
    #score = (freq*2-1) * (1000-orderscore)
    score = freq-1
    if rel == 'HasA': score -= 1
    if orderscore == 0: score += 1
    if score <= 0:
        counts['low score'] += 1
        weak_out.write(line)
        continue

    if adverb != default: counts['negated'] += 1
    count += 1
    counts['success'] += 1
    good_out.write(line)
    if make:
        frametext = "{1} " + relation[3:] + " {2}"
        rel_obj = Relation.objects.get(name=rel)
        frames = Frame.objects.filter(language=en, text=frametext, relation=rel_obj)
        if len(frames) > 0:
            # we want the first one; too bad there are duplicates right now
            frame = frames[0]
            created = False
        else:
            # fall back on what we did before
            frame, created = Frame.objects.get_or_create(language=en, text=frametext, relation=rel_obj, defaults=dict(frequency=adverb, goodness=2))
        if created: print "CREATED:", frame

        print RawAssertion.make(user, frame, left, right, activity)
    else:
        print left, relation[3:], right, score

print counts

flag_out.close()
good_out.close()
weak_out.close()
similar_out.close()

simout = open('similarity-scores.txt', 'w')
for sim in text_similarities:
    print >> simout, sim
simout.close()
