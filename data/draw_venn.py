from venn import venn
import matplotlib.pyplot as plt
import json

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10


sets = dict()

#with open('../random_sample_set.json', 'r', encoding='utf-8') as f:
#    d4j, _ = json.load(f)
d4j=[("Chart", [i for i in range(1, 27)]),
    ("Cli", [i for i in range(1, 41) if i not in [6]]),
    ("Closure", [i for i in range(1, 177) if i not in [63, 93]]),
    ("Codec", [i for i in range(1, 19)]),
    ("Collections", [i for i in range(1, 29)]),
    ("Compress", [i for i in range(1, 48)]),
    ("Csv", [i for i in range(1, 17)]),
    ("Gson", [i for i in range(1, 19)]),
    ("JacksonCore", [i for i in range(1, 27)]),
    ("JacksonDatabind", [i for i in range(1, 113) if i not in [65, 89]]),
    ("JacksonXml", [i for i in range(1, 7)]),
    ("Jsoup", [i for i in range(1, 94)]),
    ("JxPath", [i for i in range(1, 23)]),
    ("Lang", [i for i in range(1, 66) if i not in [2, 18, 25, 48]]),
    ("Math", [i for i in range(1, 107)]),
    ("Mockito", [i for i in range(1, 39)]),
    ("Time", [i for i in range(1, 28) if i not in [21]])]

other=set()
with open('data/contrastrepair.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    other.update(set(data))
with open('data/iter.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    other.update(set(data))
with open('data/selfapr.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    other.update(set(data))
sets['Others']=other
with open('data/chatapr.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    sets['ChatRepair']=set(data)
with open('data/repairagent.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    sets['RepairAgent']=set(data)
with open('data/d4c.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    sets['D4C']=set(data)
with open('data/ciallo-gpt.csv', 'r', encoding='utf-8') as f:
    lines=f.readlines()
    data = []
    for line in lines:
        if line:  # Skip empty lines
            word, num = line.split(',')
            for p, i in d4j:
                if word != p:
                    continue
                if int(num) in i:
                    data.append(line)
                    break
    sets['Ciallo']=set(data)
'''
other=set()
with open('contrastrepair.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    other.update(set(lines))
with open('iter.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    other.update(set(lines))
with open('selfapr.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    other.update(set(lines))
sets['Others']=other

with open('chatapr.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    sets['ChatRepair'] = set(lines)
with open('repairagent.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    sets['RepairAgent'] = set(lines)
with open('d4c.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    sets['D4C']=set(lines)
with open('ciallo.csv', 'r', encoding='utf-8') as f:
    lines=f.readlines()
    sets['Ciallo']=set(lines)
    print(len(set(lines)))
'''
# Draw Venn diagram
ax = venn(
    data=sets,  # Your dataset
    hint_hidden=False,  # Disable hidden hints
    legend_loc=None,  # Do not show legend
)

# Manually add set name labels (coordinates need to be adjusted according to ellipse positions)
dataset_labels = list(sets.keys())
positions = [
    (0.05, 0.75),  # Top right of the first ellipse
    (0.5, 1.0),  # Top left of the second ellipse
    (0.95, 0.75),  # Below the third ellipse
    (0.75, 0.0),  # Left of the fourth ellipse
    (0.25, 0.0)   # Right of the fifth ellipse
]  # Example coordinates
ax = plt.gca()
for label, pos in zip(sets.keys(), positions):
    ax.text(pos[0], pos[1], label, fontsize=18, ha='center', va='center',
            fontweight='bold' if label == 'Ciallo' else 'normal')

# Find the number to be bolded and modify its style
center_text = None
for text in ax.texts:
    if text.get_text() == '59':  # Adjust according to actual value
        text.set_fontweight('bold')
        text.set_fontsize(16)  # Increase font size
        center_text = text
        break

plt.tight_layout()
plt.show()