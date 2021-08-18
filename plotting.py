#!/usr/bin/python3

import sys
import base64
import binascii
import microtags
import matplotlib
import math
import numpy as np
from scipy import optimize


#
# _____________________________________________________________________________
#
def main(argv):

    import matplotlib.pyplot as plot
    globals()['plot'] = plot

    microtagList = microtags.main(argv)

    yScale = 1. / 50.
    yLabel = 'Microseconds'
    #yScale = 1.
    #yLabel = 'Ticks'

    stateTags = ['BenchNum', 'BenchSize', 'BenchRun', 'BenchVariant', 'ComprRounds', 'FinalRounds']
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
                    name = 'AES-128-GMAC (AO)'
                elif stateVec[0] == 0x21:
                    name = 'AES-256-GMAC (AO)'
                elif stateVec[0] == 0x28:
                    name = 'AES-128-GCM (AE)'
                elif stateVec[0] == 0x29:
                    name = 'AES-256-GCM (AE)'
                elif stateVec[0] == 0x30:
                    name = 'ChaCha20-Poly1305 (AO)'
                elif stateVec == (0x31, 0):
                    name = 'ChaCha20-Poly1305-initial-run'
                elif stateVec[0] == 0x31 and stateVec[1] > 0:
                    name = 'ChaCha20-Poly1305-followup-run'
                elif stateVec[0] == 0x38:
                    name = 'ChaCha20-Poly1305 (AE)'
                elif stateVec[0] == 0x40:
                    name = 'SHA3'
                elif stateVec[0] == 0x50:
                    name = 'KMAC'
                elif stateVec[0] == 0x60:
                    name = 'SipHash-{}-{}-64'.format(state['ComprRounds'], state['FinalRounds'])
                elif stateVec[0] == 0x61:
                    name = 'SipHash-{}-{}-128'.format(state['ComprRounds'], state['FinalRounds'])
                else:
                    continue

                x = state['BenchSize']
                end_time = tag.getTagData()
                start_time = microtagList.getAnalysedTags()[tag.getStartTagIndex()].getTagData()
                if end_time >= start_time:
                    y = end_time - start_time
                else:
                    y = (end_time + 0xFFFFFFFF) - start_time

                if name in data:
                    # >>> New point in existing dataset >>>
                    if x in data[name]:
                        # >>> New point at existing x value >>>
                        data[name][x] = (
                                data[name][x][0] + y, 
                                data[name][x][1] + y**2, 
                                data[name][x][2] + 1)
                    else:
                        # >>> New point at new x value >>>
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
            Y += [y * yScale]
            Yvardown += [(y - yerr) * yScale]
            Yvarup += [(y + yerr) * yScale]

        print('Plotting {0} with {1} constribution(s)'.format(name, 
                str(set([v[2] for v in data[name].values()]))))

        plot.scatter(X, Y, 2)
        plot.plot(X, Y, label=name)
        plot.fill_between(X, Yvardown, Yvarup, color='lightgrey')

        if True:
        
            # Linear fit
            B = lambda x, m, c: m*x + c

            Xnp = np.array(X)
            Ynp = np.array(Y)

            #params = [max(Ymean), 1E-5]
            params, params_covariance = optimize.curve_fit(B, X, Y, p0=[0., 0.])

            print(' -> fit: m = {0:.2f} {1}/byte, c = {2:.2f}'.format(params[0], yLabel, params[1]))

    plot.legend()

    xmin, xmax = plot.xlim()
    plot.xlim(0., xmax)
    ymin, ymax = plot.ylim()
    plot.ylim(0., ymax)


    plot.xlabel(r'Payload Size')
    plot.ylabel(yLabel)

    plot.grid(which='major', color='#DDDDDD', linewidth=0.9)
    plot.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.7)
    plot.minorticks_on()
    plot.title("ARM Cortex-M4, STM32F429 @100 MHz, mbedTLS 2.16.2")

    plot.show()


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);

