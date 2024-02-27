import os
import matplotlib.pyplot as plt
import numpy as np


Cat = 'Partially Specified Uniform Random FSM'

D = ['20231209_175034_898469',
     '20231209_175054_807864',
     '20231209_175122_640336',
     '20231209_175144_429325',
     '20231209_175212_512773']


Fs = {'20231209_175034_898469': 'FSM 1',
      '20231209_175054_807864': 'FSM 2',
      '20231209_175122_640336': 'FSM 3',
      '20231209_175144_429325': 'FSM 4',
      '20231209_175212_512773': 'FSM 5'}




def get_uios():
    data = {}
    for d in Fs:
        f = os.path.join(d, d+'_uio.txt')
        with open(f, 'r') as fn:
            uios = fn.readline()
            uios = eval(uios)
            data[d] = uios
    return data




def count_uios(data):
    results = {}
    for d in data:
        uios = data[d]
        states = sorted(uios)
        collection = {}
        for s in states:
            s_label = 'S'+str(s)
            num_of_uios = len(uios[s])
            collection[s_label] = num_of_uios
        results[d] = collection

    return results
        


def plot_uios(d, UIOs):
    labels = list(UIOs.keys())
    values = list(UIOs.values())

    min_val, max_val = min(values), max(values)
    l = 'Numbers of UOs: Min={}, Max={}'
    
    height = values
    bars = labels
    x_pos = np.arange(len(bars))

    plt.bar(x_pos, height, color=['blue'], align='edge', width=0.4)
    plt.xticks(x_pos, bars, rotation=75, fontsize=5, fontname='serif')
    plt.legend([l.format(min_val, max_val)])

    plt.xlabel("FSM States")
    plt.ylabel("Number of UIOs")

    plt.title('UIOs Constructed from '+Cat)


    plt.show()
    return

    fname = Cat.split()[:4] + [Fs[d]]
    fname = '_'.join(fname)
    fname = fname.replace(' ', '_') + '.png'
    plt.savefig(fname)


data = get_uios()

results = count_uios(data)

for k in results:
    plot_uios(k, results[k])
