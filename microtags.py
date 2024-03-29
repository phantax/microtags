#!/usr/bin/python3

import sys
import base64
import binascii


#
# _____________________________________________________________________________
#
class TextFormatter(object):

    useColor = True

    strColorEnd = '\033[0m'

    @staticmethod
    def makeBoldWhite(s):
        if TextFormatter.useColor:
            return '\033[1m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldRed(s):
        if TextFormatter.useColor:
            return '\033[1;31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldGreen(s):
        if TextFormatter.useColor:
            return '\033[1;32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldYellow(s):
        if TextFormatter.useColor:
            return '\033[1;33m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldBlue(s):
        if TextFormatter.useColor:
            return '\033[1;34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldPurple(s):
        if TextFormatter.useColor:
            return '\033[1;35m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldCyan(s):
        if TextFormatter.useColor:
            return '\033[1;36m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeGreen(s):
        if TextFormatter.useColor:
            return '\033[32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeRed(s):
        if TextFormatter.useColor:
            return '\033[31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBlue(s):
        if TextFormatter.useColor:
            return '\033[34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def indent(str, level=1):
        lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
        return '\n'.join(lines)


#
# _____________________________________________________________________________
#
class Microtag(object):

    def __init__(self, microtag=None):
        if microtag is None:
            self.tagData = None
            self.tagId = None
        else:
            self.tagData = microtag.getTagData()
            self.tagId = microtag.getTagId()

    def __str__(self):
        if self.tagData is None or self.tagId is None:
            raise Exception('Undefined microtag')
        return '{0:04X}:{1:08X}'.format(self.tagId, self.tagData)

    def getTagData(self):
        return self.tagData

    def getTagId(self):
        return self.tagId

    def importFromCode(self, code):

        # code must be a string of length 8
        if not isinstance(code, str) or len(code) != 8:
            raise Exception('Invalid code "{0}"'.format(code))

        # extract data and id from base64-encoded tag
        hexCode = binascii.hexlify(base64.b64decode(code))
        self.tagData = int(hexCode[0:8], base = 16)
        self.tagId = int(hexCode[8:12], base = 16)

    def exportCode(self):
        hexCode = '{0:08X}{1:04X}'.format(self.tagData, self.tagId)
        return hexCode.encode('base64')


#
# _____________________________________________________________________________
#
class MicrotagUntyped(Microtag):

    def __init__(self, tag=None, idAlias=None):
        Microtag.__init__(self, tag)
        self.idAlias = idAlias
        self.index = None

    def setIdAlias(self, idAlias):
        self.idAlias = idAlias

    def getIdAlias(self):
        return self.idAlias

    def setIndex(self, index):
        self.index = index

    def getIndex(self):
        return self.index


#
# _____________________________________________________________________________
#
class MicrotagTickBased(MicrotagUntyped):

    def __init__(self, tag=None, idAlias=None):
        MicrotagUntyped.__init__(self, tag, idAlias)


#
# _____________________________________________________________________________
#
class MicrotagStart(MicrotagTickBased):

    def __init__(self, tag=None, idAlias=None):
        MicrotagTickBased.__init__(self, tag, idAlias)
        self.stopTagIndex = None

    def setStopTagIndex(self, index):
        self.stopTagIndex = index

    def getStopTagIndex(self):
        return self.stopTagIndex


#
# _____________________________________________________________________________
#
class MicrotagStop(MicrotagTickBased):

    def __init__(self, tag=None, idAlias=None):
        MicrotagTickBased.__init__(self, tag, idAlias)
        self.startTagIndex = None

    def setStartTagIndex(self, index):
        self.startTagIndex = index

    def getStartTagIndex(self):
        return self.startTagIndex


#
# _____________________________________________________________________________
#
class MicrotagEvent(MicrotagTickBased):

    def __init__(self, tag=None, idAlias=None):
        MicrotagTickBased.__init__(self, tag, idAlias)


#
# _____________________________________________________________________________
#
class MicrotagData(MicrotagUntyped):

    def __init__(self, tag=None, idAlias=None):
        MicrotagUntyped.__init__(self, tag, idAlias)


#
# _____________________________________________________________________________
#
class MicrotagVarData(MicrotagData):

    def __init__(self, tag=None, idAlias=None):
        MicrotagData.__init__(self, tag, idAlias)
        self.previous = None
        self.length = None
        self.data = None
        self.isLast = False

    def setPrevious(self, previous):
        self.previous = previous

    def getIndex(self):
        if self.previous is None:
            return 0
        else:
            return self.previous.getIndex() + 1

    def getLength(self):
        if self.previous is None:
            return self.length
        else:
            return self.previous.getLength()

    def setIsLast(self, isLast):
        self.isLast = isLast

    def getIsLast(self):
        return self.isLast

    def getData(self):
        if self.previous is None:
            return self.data
        else:
            return self.previous.getData() + self.data

    def processVarData(self):
        if self.getIndex() == 0:
            self.length = (self.getTagData() & 0xFF000000) >> 24
            self.data = (self.getTagData() & 0x00FFFFFF) \
                    .to_bytes(3, byteorder='big')[:self.length]
        else:
            self.data = self.getTagData().to_bytes(4, byteorder='big') \
                    [:self.getLength() - 4*self.getIndex()]
            if self.getLength() - 4*self.getIndex() < 4:
                self.setIsLast(True)


#
# _____________________________________________________________________________
#
class MicrotagList(object):

    def __init__(self, dataToTime=None):
        self.rawTags = []
        self.analysedTags = None
        self.tagDefDict = {}

        # conversion function from data (ticks) to time
        if dataToTime is not None:
            self.dataToTime = dataToTime
        else:
            # the default is using ticks
            self.dataToTime = lambda c: (c, 'ticks', 0)

    def dataToTimeStr(self, data):
        time = self.dataToTime(data)
        return '{0:,.{2}f} {1}'.format(time[0], time[1], time[2]) 

    def dataToTimeDiffStr(self, dataStart, dataStop):
        timeStart = self.dataToTime(dataStart)
        timeStop = self.dataToTime(dataStop)
        return '{0:,.{2}f} {1}'.format(
                timeStop[0] - timeStart[0], timeStop[1], timeStop[2])

    def getRawTags(self):
        return self.rawTags

    def getAnalysedTags(self):
        return self.analysedTags

    def analyse(self):

        # start off with an empty list of analysed microtags
        self.analysedTags = []

        # a list of indices referring to unmatched start tags
        unmatchedStarts = []

        # iterate over all raw microtags
        for i, tag in enumerate(self.getRawTags()):

            if tag.getTagId() in self.tagDefDict:

                # microtag id alias from dictionary
                idAlias = self.tagDefDict[tag.tagId]

                # extract microtag type (start, stop, event, data)
                if idAlias.startswith('start:'):
                    analysedTag = MicrotagStart(tag, idAlias[6:])
                elif idAlias.startswith('stop:'):
                    analysedTag = MicrotagStop(tag, idAlias[5:])
                elif idAlias.startswith('event:'):
                    analysedTag = MicrotagEvent(tag, idAlias[6:])
                elif idAlias.startswith('data:'):
                    analysedTag = MicrotagData(tag, idAlias[5:])
                elif idAlias.startswith('vardata:'):
                    analysedTag = MicrotagVarData(tag, idAlias[8:])
                else:
                    analysedTag = MicrotagUntyped(tag, idAlias)

            else:
                analysedTag = MicrotagUntyped(tag)

          
            if isinstance(analysedTag, MicrotagStart):

                # add indices of start tags to list of unmatched start tags
                unmatchedStarts += [i]

            elif isinstance(analysedTag, MicrotagStop):

                # find corresponding start tag
                matchingStarts = [j for j in unmatchedStarts[::-1] \
                        if isinstance(self.getAnalysedTags()[j], MicrotagStart) \
                        and self.getAnalysedTags()[j].getIdAlias() == analysedTag.getIdAlias()]
                if len(matchingStarts) > 0:

                    del unmatchedStarts[unmatchedStarts.index(matchingStarts[0])]

                    analysedTag.setStartTagIndex(matchingStarts[0])
                    self.getAnalysedTags()[matchingStarts[0]].setStopTagIndex(i)

            elif isinstance(analysedTag, MicrotagVarData):
    
                previousTag = None
                if len(self.getAnalysedTags()) > 0:
                    previousTag = self.getAnalysedTags()[-1]
                if isinstance(previousTag, MicrotagVarData) and \
                        previousTag.getIdAlias() == analysedTag.getIdAlias() and \
                        not previousTag.getIsLast():
                    analysedTag.setPrevious(previousTag)

                analysedTag.processVarData()

            self.analysedTags += [analysedTag]

    def __len__(self):
        return len(self.rawTags)

    def __str__(self):

        # prepare output as a list of lines
        lines = []

        # determine length of longest string in tag id alias dictionary
        # (removing leading type definitions, if present)
        widthId = max([len(s if s.find(':') == -1 else s[s.find(':')+1:]) \
                for s in list(self.tagDefDict.values())] + [8]) + 4

        # determine length of highest tag index
        widthIndex = len('{0}'.format(len(self.getAnalysedTags())))

        for i, tag in enumerate(self.getAnalysedTags()):

            # ===== tag index =====

            line = '{0:{1}}: '.format(i, widthIndex)

            # ===== tag id or id alias =====

            if isinstance(tag, MicrotagStart):
                tagType = '<'
                idAlias = TextFormatter.makeBoldGreen('{0:{1}}' \
                        .format(tag.getIdAlias(), widthId + 2))
            elif isinstance(tag, MicrotagStop):
                tagType = '>'
                idAlias = TextFormatter.makeBoldRed('{0:{1}}' \
                        .format(tag.getIdAlias(), widthId + 2))
            elif isinstance(tag, MicrotagEvent):
                tagType = '!'
                idAlias = TextFormatter.makeBoldYellow('{0:{1}}' \
                        .format(tag.getIdAlias(), widthId + 2))
            elif isinstance(tag, MicrotagVarData):
                tagType = 'V'
                idAlias = TextFormatter.makeBoldBlue('{0:{1}}' \
                        .format('{0}<{1}>'.format(tag.getIdAlias(), tag.getIndex()), widthId + 2))
            elif isinstance(tag, MicrotagData):
                tagType = 'D'
                idAlias = TextFormatter.makeBoldBlue('{0:{1}}' \
                        .format(tag.getIdAlias(), widthId + 2))
            else:
                tagType = '?'                    
                if tag.getIdAlias() is not None:
                    idAlias = tag.getIdAlias()
                else:
                    idAlias = '[0x{0:04X}]'.format(tag.getTagId())
                idAlias = '{0:{1}}'.format(idAlias, widthId + 2)

            line += tagType + ' ' + idAlias
        
            # ===== tag content, i.e. time or data =====  

            if isinstance(tag, MicrotagTickBased):
                line += '{0:>25}  '.format(self.dataToTimeStr(tag.tagData))
            elif isinstance(tag, MicrotagVarData):
                if tag.getIsLast():
                    hexVal = ''.join(['{0:02X}'.format(b) for b in tag.getData()])
                    line += TextFormatter.makeBoldBlue('[ 0x{0} ]'.format(hexVal))
                else:
                    line += TextFormatter.makeBoldBlue('...')
            else:
                line += TextFormatter.makeBoldBlue('[ 0x{0:08X} ]  '.format(tag.tagData))
        
            # ===== start/stop tag matching =====  
        
            if isinstance(tag, MicrotagStart):

                # matching string
                line += '--->[ {0:{1}} ]' \
                        .format(str(tag.getStopTagIndex()), widthIndex)

            elif isinstance(tag, MicrotagStop):

                # matching string
                line += '[ {0:{1}} ]---({2:^{3}})--->[ {4:{1}} ]' \
                        .format(str(tag.getStartTagIndex()), widthIndex, tag.getIdAlias(), widthId, i)
                # time difference
                line += '{0:>20}'.format(self.dataToTimeDiffStr(
                        self.getAnalysedTags()[tag.getStartTagIndex()].getTagData(), tag.getTagData()))

            lines += [line]

        return '\n'.join(lines)

    def __iter__(self):
        return iter(self.rawTags)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.rawTags[index]

    def importTagsFromCodes(self, codes):
        lenBefore = len(self.rawTags)
        for code in codes.split('\n'):
            try:
                tag = Microtag()
                tag.importFromCode(code)
                self.rawTags += [tag]
            except Exception as e:
                print(e)
                pass
        # return the number of tags imported
        return len(self.rawTags) - lenBefore

    def importTagsFromFile(self, filename):
        f = open(filename, 'r')
        lines = [line.strip() for line in f]
        codes = '\n'.join([line for line in lines
                if len(line) == 8 and line[0] != '#'])
        f.close()
        if len(codes) > 0:
            return self.importTagsFromCodes(codes)
        else:
            return 0

    def importTagDefsFromFile(self, filename):
        f = open(filename, 'r')
        lines = [line.strip() for line in f]
        tagDefs = [line for line in lines
                if len(line) > 0 and line[0] != '#']
        f.close()

        nBefore = len(self.tagDefDict)

        for tagDef in tagDefs:
            tokens = [token.strip() for token in tagDef.split(',')]
            if len(tokens) != 2:
                # >>> invalid line >>>
                continue
            if not tokens[0].startswith('0x'):
                # >>> invalid line >>>
                continue

            self.tagDefDict[int(tokens[0][2:], base = 16)] = tokens[1]

        return len(self.tagDefDict) - nBefore

    def printList(self):
        pass


#
# _____________________________________________________________________________
#
def main(argv):

    if len(argv) == 2:
        tagDefFilename = argv[0]
        tagsFilename = argv[1]
    else:
        print("Wrong number of arguments. Stopping.")
        print("Expecting <tag-def-file> <tag-file>")
        return

    # read input file
    microtags = MicrotagList() #, lambda c: (c / 84E6, 's', 3))

    try:
        n = microtags.importTagDefsFromFile(tagDefFilename)
        print(('Imported {0} microtag definition(s).'.format(n)))
    except Exception as e:
        print("Failed to read/parse input file. Stopping.")
        print(e)
        return

    try:
        n = microtags.importTagsFromFile(tagsFilename)
        print(('Imported {0} microtag(s).'.format(n)))
    except Exception as e:
        print("Failed to read/parse input file. Stopping.")
        print(e)
        return

    microtags.analyse()

    print(microtags)

    return microtags


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);

