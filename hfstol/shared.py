import struct
from typing import List

from .constants import *


class Header:
    """Read and provide interface to header"""

    def __init__(self, file):
        byte_buffer = file.read(5)  # "HFST\0"
        if struct.unpack_from("<5s", byte_buffer, 0)[0] == b'HFST\x00':
            # just ignore any hfst3 header
            remaining = struct.unpack_from("<H", file.read(3), 0)[0]
            self._handle_hfst3_header(file, remaining)
            byte_buffer = file.read(56)  # 2 unsigned shorts, 4 unsigned ints and 9 uint-bools
        else:
            byte_buffer = byte_buffer + file.read(56 - 5)
        self.number_of_input_symbols = struct.unpack_from("<H", byte_buffer, 0)[0]
        self.number_of_symbols = struct.unpack_from("<H", byte_buffer, 2)[0]
        self.size_of_transition_index_table = struct.unpack_from("<I", byte_buffer, 4)[0]
        self.size_of_transition_target_table = struct.unpack_from("<I", byte_buffer, 8)[0]
        self.number_of_states = struct.unpack_from("<I", byte_buffer, 12)[0]
        self.number_of_transitions = struct.unpack_from("<I", byte_buffer, 16)[0]
        self.weighted = struct.unpack_from("<I", byte_buffer, 20)[0] != 0
        self.deterministic = struct.unpack_from("<I", byte_buffer, 24)[0] != 0
        self.input_deterministic = struct.unpack_from("<I", byte_buffer, 28)[0] != 0
        self.minimized = struct.unpack_from("<I", byte_buffer, 32)[0] != 0
        self.cyclic = struct.unpack_from("<I", byte_buffer, 36)[0] != 0
        self.has_epsilon_epsilon_transitions = struct.unpack_from("<I", byte_buffer, 40)[0] != 0
        self.has_input_epsilon_transitions = struct.unpack_from("<I", byte_buffer, 44)[0] != 0
        self.has_input_epsilon_cycles = struct.unpack_from("<I", byte_buffer, 48)[0] != 0
        self.has_unweighted_input_epsilon_cycles = struct.unpack_from("<I", byte_buffer, 52)[0] != 0

    def _handle_hfst3_header(self, file, remaining):
        chars = struct.unpack_from("<" + str(remaining) + "c",
                                   file.read(remaining), 0)
        # assume the h3-header doesn't say anything surprising for now


class Alphabet:
    """Read and provide interface to alphabet"""

    def __init__(self, file, number_of_symbols):
        key_table = []  # type: List[str]
        flag_diacritic_operations = dict()  # of symbol numbers to string triples

        for x in range(number_of_symbols):

            symbol = b""

            while True:
                byte = file.read(1)
                if byte == b'\0':  # a symbol has ended
                    # symbol = unicode(symbol, "utf-8")
                    symbol_str = symbol.decode(encoding='utf-8')
                    if len(symbol_str) > 4 and symbol_str[0] == '@' and \
                            symbol_str[-1] == '@' and symbol_str[2] == '.' and symbol_str[1] in "PNRDCU":
                        # this is a flag diacritic
                        op = feat = val = ""
                        parts = symbol_str[1:-1].split('.')
                        if len(parts) == 2:
                            op, feat = parts
                        elif len(parts) == 3:
                            op, feat, val = parts
                        else:

                            key_table.append(symbol_str)
                            break
                        flag_diacritic_operations[x] = FlagDiacriticOperation(op, feat, val)
                        key_table.append("")
                        break
                    key_table.append(symbol_str)
                    break
                symbol += byte
        key_table[0] = ""
        self.key_table = key_table
        self.flagDiacriticOperations = flag_diacritic_operations


class LetterTrie:
    """Insert and prefix-retrieve string / symbol number pairs"""

    class Node:

        def __init__(self):
            self.symbols = dict()
            self.children = dict()

        def add(self, string, symbolNumber):
            """
            Add string to trie, having it resolve to symbolNumber
            """
            if len(string) > 1:
                if not (string[0] in self.children):
                    self.children[string[0]] = self.__class__()  # instantiate a new node
                self.children[string[0]].add(string[1:], symbolNumber)
            elif len(string) == 1:
                self.symbols[string[0]] = symbolNumber
            else:
                self.symbols[string] = symbolNumber

        def find(self, indexstring):
            """
            Find symbol number corresponding to longest match in indexstring
            (starting from the position held by indexstring.pos)
            """
            if indexstring.pos >= len(indexstring.s):
                return NO_SYMBOL_NUMBER
            current = indexstring.get()
            indexstring.pos += 1
            if not (current in self.children):
                if not (current in self.symbols):
                    indexstring.pos -= 1
                    return NO_SYMBOL_NUMBER
                return self.symbols[current]
            temp = self.children[current].find(indexstring)
            if temp == NO_SYMBOL_NUMBER:
                if not (current in self.symbols):
                    indexstring.pos -= 1
                    return NO_SYMBOL_NUMBER
                return self.symbols[current]
            return temp

    def __init__(self):
        self.root = self.Node()

    def addString(self, string, symbolNumber):
        self.root.add(string, symbolNumber)

    def findKey(self, indexstring):
        return self.root.find(indexstring)


class Indexlist:
    """Utility class to keep track of where we are in a list"""

    def __init__(self, items=[]):
        self.s = list(items)
        self.pos = 0

    def get(self, adjustment=0):
        return self.s[self.pos + adjustment]

    def put(self, val, adjustment=0):
        if (self.pos + adjustment) < len(self.s):
            self.s[self.pos + adjustment] = val
        else:
            self.s.append(val)

    def save(self):
        self.temp = self.pos

    def restore(self):
        self.pos = self.temp

    def last(self):
        if len(self.s) > 0:
            return self.s[-1]
        return None


class FlagDiacriticOperation:
    """Represents one flag diacritic operation"""

    def __init__(self, op, feat, val):
        self.operation = op
        self.feature = feat
        self.value = val


class FlagDiacriticStateStack:
    """The combined state for all flag diacritics"""

    def __init__(self):
        self.stack = [dict()]

    def clear(self):
        self.stack = [dict()]

    def pop(self):
        self.stack.pop()

    def duplicate(self):
        self.stack.append(self.stack[-1].copy())

    def push(self, flag_diacritic):
        """
        Attempt to modify flag diacritic state stack. If successful, push new
        state and return True. Otherwise return False.
        """
        if flag_diacritic.operation == 'P':  # positive set
            self.duplicate()
            self.stack[-1][flag_diacritic.feature] = (flag_diacritic.value, True)
            return True
        if flag_diacritic.operation == 'N':  # negative set
            self.duplicate()
            self.stack[-1][flag_diacritic.feature] = (flag_diacritic.value, False)
            return True
        if flag_diacritic.operation == 'R':  # require
            if flag_diacritic.value == '':  # empty require
                if self.stack[-1].get(flag_diacritic.feature) is None:
                    return False  # empty require = require nonempty value
                else:
                    self.duplicate()
                    return True
            if self.stack[-1].get(flag_diacritic.feature) == (flag_diacritic.value, True):
                self.duplicate()
                return True
            return False
        if flag_diacritic.operation == 'D':  # disallow
            if flag_diacritic.value == '':  # empty disallow
                if self.stack[-1].get(flag_diacritic.feature) is None:
                    self.duplicate()
                    return True
                else:
                    return False
            if self.stack[-1].get(flag_diacritic.feature) == (flag_diacritic.value, True):
                return False
            self.duplicate()
            return True
        if flag_diacritic.operation == 'C':  # clear
            self.duplicate()
            if flag_diacritic.feature in self.stack[-1]:
                del self.stack[-1][flag_diacritic.feature]
            return True
        if flag_diacritic.operation == 'U':  # unification
            if not flag_diacritic.feature in self.stack[-1] or \
                    self.stack[-1][flag_diacritic.feature] == (flag_diacritic.value, True) or \
                    (self.stack[-1][flag_diacritic.feature][1] == False and \
                     self.stack[-1][flag_diacritic.feature][0] != flag_diacritic.value):
                self.duplicate()
                self.stack[-1][flag_diacritic.feature] = (flag_diacritic.value, True)
                return True
            return False


def match(transition_symbol, input_symbol):
    """Utility function to check whether we want to traverse a transition/index"""
    if transition_symbol == NO_SYMBOL_NUMBER:
        return False
    if input_symbol == NO_SYMBOL_NUMBER:
        return True
    return transition_symbol == input_symbol
