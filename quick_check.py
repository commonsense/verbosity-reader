cheat_count = total_count = 0
for line in open('verbosity.txt'):
    parts = line.strip().split('\t')
    left, relation, right, freq, orderscore = parts[:5]
    clue_words = right.split()
    if left in clue_words:
        print line.strip()
        cheat_count += 1
    total_count += 1
print cheat_count, '/', total_count
