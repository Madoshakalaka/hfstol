from typing import List, Any

from .constants import *
from .shared import match, Indexlist, LetterTrie, FlagDiacriticStateStack
import struct


class Transducer:
    class TransitionIndex:

        def __init__(self, input_symbol, transition):
            self.inputSymbol = input_symbol
            self.target = transition

        def matches(self, symbol):
            return match(self.inputSymbol, symbol)

        def isFinal(self):
            return self.inputSymbol == NO_SYMBOL_NUMBER and \
                   self.target != NO_TABLE_INDEX

    class IndexTable:

        def __init__(self, file, number_of_indices):
            byte_buffer = file.read(number_of_indices * 6)  # ushort + uint
            self.indices = \
                [Transducer.TransitionIndex(*struct.unpack_from("<HI", byte_buffer, x * 6)) \
                 for x in range(number_of_indices)]

    class Transition:

        def __init__(self, input, output, target):
            self.inputSymbol = input
            self.outputSymbol = output
            self.target = target

        def matches(self, symbol):
            return match(self.inputSymbol, symbol)

        def isFinal(self):
            return self.inputSymbol == NO_SYMBOL_NUMBER and \
                   self.outputSymbol == NO_SYMBOL_NUMBER and \
                   self.target == 1

    class TransitionTable:

        def __init__(self, file, number_of_transitions):
            self.position = 0
            byte_buffer = file.read(number_of_transitions * 8)  # 2*ushort + uint
            self.transitions = \
                [Transducer.Transition(*struct.unpack_from("<HHI", byte_buffer, x * 8)) \
                 for x in range(number_of_transitions)]

        def set(self, pos):
            if pos >= TRANSITION_TARGET_TABLE_START:
                self.position = pos - TRANSITION_TARGET_TABLE_START
            else:
                self.position = pos

        def at(self, pos):
            return self.transitions[pos - TRANSITION_TARGET_TABLE_START]

        def isFinal(self, pos):
            if pos >= TRANSITION_TARGET_TABLE_START:
                return self.transitions[pos - TRANSITION_TARGET_TABLE_START].isFinal()
            return self.transitions[pos].isFinal()

    def __init__(self, file, header, alphabet):
        self.alphabet = alphabet
        self.flagDiacriticOperations = alphabet.flagDiacriticOperations
        self.stateStack = FlagDiacriticStateStack()
        self.letterTrie = LetterTrie()
        for x in range(header.number_of_symbols):
            self.letterTrie.addString(alphabet.key_table[x], x)
        self.indexTable = self.IndexTable(file, header.size_of_transition_index_table)
        self.indices = self.indexTable.indices
        self.transitionTable = self.TransitionTable(file, header.size_of_transition_target_table)
        self.transitions = self.transitionTable.transitions
        self.displayVector = []
        self.outputString = Indexlist()
        self.inputString = Indexlist()
        self.output_list = []  # type: List[str]

    def tryEpsilonIndices(self, index):
        if self.indices[index].inputSymbol == 0:
            self.tryEpsilonTransitions(self.indices[index].target - TRANSITION_TARGET_TABLE_START)

    def tryEpsilonTransitions(self, index):
        while True:
            if self.transitions[index].inputSymbol == 0:
                self.outputString.put(self.transitions[index].outputSymbol)
                self.outputString.pos += 1
                self.getAnalyses(self.transitions[index].target)
                self.outputString.pos -= 1
                index += 1
            elif self.transitions[index].inputSymbol in self.flagDiacriticOperations:
                if not self.stateStack.push(self.flagDiacriticOperations[self.transitions[index].inputSymbol]):
                    index += 1
                    continue  # illegal state modification; do nothing
                else:
                    self.outputString.put(self.transitions[index].outputSymbol)
                    self.outputString.pos += 1
                    self.getAnalyses(self.transitions[index].target)
                    self.outputString.pos -= 1
                    index += 1
                    self.stateStack.pop()
                    continue
            else:
                return

    def findIndex(self, index):
        if self.indices[index + self.inputString.get(-1)].inputSymbol == self.inputString.get(-1):
            self.findTransitions(self.indices[index + self.inputString.get(-1)].target - TRANSITION_TARGET_TABLE_START)

    def findTransitions(self, index):
        while self.transitions[index].inputSymbol != NO_SYMBOL_NUMBER:
            if self.transitions[index].inputSymbol == self.inputString.get(-1):
                self.outputString.put(self.transitions[index].outputSymbol)
                self.outputString.pos += 1
                self.getAnalyses(self.transitions[index].target)
                self.outputString.pos -= 1
            else:
                return
            index += 1

    def getAnalyses(self, index):
        if index >= TRANSITION_TARGET_TABLE_START:
            index -= TRANSITION_TARGET_TABLE_START
            self.tryEpsilonTransitions(index + 1)
            if self.inputString.get() == NO_SYMBOL_NUMBER:
                if self.transitionTable.isFinal(index):
                    self.noteAnalysis()
                self.outputString.put(NO_SYMBOL_NUMBER)
                return
            self.inputString.pos += 1
            self.findTransitions(index + 1)
        else:
            self.tryEpsilonIndices(index + 1)
            if self.inputString.get() == NO_SYMBOL_NUMBER:
                if self.indices[index].isFinal():
                    self.noteAnalysis()
                self.outputString.put(NO_SYMBOL_NUMBER)
                return
            self.inputString.pos += 1
            self.findIndex(index + 1)
        self.inputString.pos -= 1
        self.outputString.put(NO_SYMBOL_NUMBER)

    def noteAnalysis(self):
        output = ""

        symbol_list = []
        for x in self.outputString.s:

            if x == NO_SYMBOL_NUMBER:
                break
            key = self.alphabet.key_table[x]
            if key != '':
                output += key
                symbol_list.append(key)

        self.output_list.append(symbol_list)

        self.displayVector.append((output, 0.0))

    def analyze(self, string):
        self.outputString = Indexlist([NO_SYMBOL_NUMBER])
        self.output_list = []

        input_line = Indexlist(string)  # wrap the input in an indexing container
        while input_line.pos < len(input_line.s) and \
                self.inputString.last != NO_SYMBOL_NUMBER:
            self.inputString.s.append(self.letterTrie.findKey(input_line))
        if self.inputString.s[-1] == NO_SYMBOL_NUMBER:
            return False
        self.inputString.s.append(NO_SYMBOL_NUMBER)
        self.getAnalyses(0)  # start at index zero
        self.displayVector = []
        self.outputString = Indexlist()
        self.inputString = Indexlist()
        self.stateStack.clear()

        return True  # if we get here, we're done analyzing

    def printAnalyses(self):
        for x in self.displayVector:
            print('\t' + x[0] + '\t' + str(x[1]))
