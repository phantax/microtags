#!/usr/bin/python3

import sys
import base64
import binascii
import microtags
import matplotlib
import math
import random


#
# _____________________________________________________________________________
#
def main(argv):

    import matplotlib.pyplot as plot
    globals()['plot'] = plot

    microtagList = microtags.main(argv)

    stateTags = ['BenchNum', 'BenchSize', 'BenchRun', 'BenchVariant']
    plotTags = ['Benchmark']

    state = {}

    # data: name -> (x value -> (Ysum, Ysum2, N))
    data = {}

    for tag in microtagList.analysedTags:

        if isinstance(tag, microtags.MicrotagData):
            if tag.getIdAlias() in stateTags:

                if tag.getIdAlias() == 'BenchNum' and \
                        state.get(tag.getIdAlias(), 0) > tag.getTagData():
                    state['BenchNum_overflow'] = state.get('BenchNum_overflow', 0) + 1

                state[tag.getIdAlias()] = tag.getTagData()                


        if isinstance(tag, microtags.MicrotagStop):
            if tag.getIdAlias() in plotTags:

                stateVec = (state['BenchVariant'], state['BenchRun'])

                if stateVec[0] == 0x10:
                    name = 'HMAC-SHA256'
                elif stateVec == (0x11, 0):
                    name = 'HMAC-SHA256-initial-run'
                elif stateVec[0] == 0x11 and stateVec[1] > 0:
                    name = 'HMAC-SHA256-followup-run'
                elif stateVec[0] == 0x20:
                    name = 'AES-GMAC-128'
                elif stateVec[0] == 0x30:
                    name = 'ChaCha20-Poly1305'
                else:
                    continue

                x = state['BenchSize']
                y = tag.getTagData() - microtagList.getAnalysedTags()[tag.getStartTagIndex()].getTagData()

                if name in data:
                    # >>> New point in existing dataset >>>
                    if x in data[name]:
                        data[name][x] = (
                                data[name][x][0] + y, 
                                data[name][x][1] + y**2, 
                                data[name][x][2] + 1)
                    else:
                        data[name][x] = (y, y**2, 1)
                else:
                    # >>> New point opens new dataset >>>
                    data[name] = { x: (y, y**2, 1) }

    for name in data:
        X = []
        Y = []
        Yvardown = []
        Yvarup = []

        for x in sorted(data[name].keys()):
            ysum = data[name][x][0]
            ysum2 = data[name][x][1]
            n = data[name][x][2]
 
            y = ysum / n
            yerr = math.sqrt( (ysum2 - ysum**2 / n) / (n - 1) ) if n > 1 else 0.

            X += [x]
            Y += [y]
            Yvardown += [y - yerr]
            Yvarup += [y + yerr]

        print('Plotting {0} with {1} constribution(s)'.format(name, 
                str(set([v[2] for v in data[name].values()]))))

        plot.scatter(X, Y, 2)
        plot.plot(X, Y, label=name)
        plot.fill_between(X, Yvardown, Yvarup, color='lightgrey')

    legend = plot.legend(frameon=1, bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           mode="expand", ncol=3, borderaxespad=0., prop={'size': 18})
    frame = legend.get_frame()
    frame.set_facecolor('white')
    frame.set_edgecolor('black')

    xmin, xmax = plot.xlim()
    plot.xlim(0., xmax)
    ymin, ymax = plot.ylim()
    plot.ylim(0., ymax)


    plot.xlabel(r'Payload Size')
    plot.ylabel(r'Ticks')

    plot.show()


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);

