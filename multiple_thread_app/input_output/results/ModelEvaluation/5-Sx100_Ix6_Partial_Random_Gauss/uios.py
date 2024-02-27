import os
import matplotlib.pyplot as plt
import numpy as np


Cat = 'Partially Specified Normal Random FSM'

D = ['20231215_175305_501001',
     '20231215_180840_082010',
     '20231215_175345_652119',
     '20231215_175413_194836',
     '20231215_180934_236959']


Fs = {'20231215_175305_501001': 'FSM 1',
      '20231215_180840_082010': 'FSM 2',
      '20231215_175345_652119': 'FSM 3',
      '20231215_175413_194836': 'FSM 4',
      '20231215_180934_236959': 'FSM 5'}




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

    plt.title('UIOs Constructed from ' + Cat)


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
