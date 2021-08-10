#!/usr/bin/python

import sys
import base64
import binascii
import microtags
import matplotlib



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

    # key -> (name, X, Y)
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
                elif stateVec == (0x11, 1):  # BenchRun in [1 .. ]
                    name = 'HMAC-SHA256-followup-run'
                elif stateVec == (0x20, 0):  # BenchRun in [0 .. ]
                    name = 'AES-GMAC-128'
                else:
                    continue

                x = [state['BenchSize']]
                y = [tag.getTagData() - microtagList.getAnalysedTags()[tag.getStartTagIndex()].getTagData()]

                if name in data:
                    data[name] = (name, data[name][1] + [x], data[name][2] + [y])
                else:
                    data[name] = (name, [x], [y])

    for name in data:
        plot.scatter(data[name][1], data[name][2], 2, label=name)
        plot.plot(data[name][1], data[name][2])

    legend = plot.legend(frameon=1, bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           mode="expand", ncol=2, borderaxespad=0., prop={'size': 18})
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

