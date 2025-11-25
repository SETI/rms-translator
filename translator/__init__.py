################################################################################
# translator.py
#
# An abstract class and subclasses for mapping strings such as file paths to
# other information. It is implemented in several ways including Python
# dictionaries and regular expression/substitution pairs.
################################################################################

import re

try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    __version__ = 'Version unspecified'  # pragma: no cover


class Translator(object):
    """Abstract class to define translators from a set of strings (such as file
    paths) to associated information.

    All subclasses implement the following methods:

        - Translator.all(strings, strings_first=False)
        - Translator.first(strings, strings_first=False)

    Input is a list of strings. The Translator object tests each string and
    determines if it passes a test. If it does pass the test, then one or more
    "translated" strings are returned.

    Translator.all() returns every translated string. Translator.first() returns
    the first translated string.

    Parameters:
        strings: A string or list of strings to translate.
        strings_first: If True, every test is applied to the first string, then
            every test is applied to the second string, etc. If False, the first
            test is applied to every string, then the second test is applied to
            every string, etc. This can affect the order of the translated
            strings returned by all(), or the single translated string that is
            returned by first().
    """

    def __add__(self, other):
        """Add two translators together using the + operator.

        Parameters:
            other: A Translator object to append.

        Returns:
            A new Translator combining self and other.
        """
        return self.append(other)

    def __iadd__(self, other):
        """Add two translators together using the += operator.

        Parameters:
            other: A Translator object to append.

        Returns:
            A new Translator combining self and other.
        """
        return self.append(other)

################################################################################
################################################################################


class TranslatorBySequence(Translator):
    """Translator defined by a sequence of other translators."""

    TAG = 'SEQUENCE'

    def __init__(self, args):
        """Initialize a TranslatorBySequence.

        Parameters:
            args: A sequence of Translator objects to apply in order.
        """
        for arg in args:
            assert isinstance(arg, Translator)

        self.sequence = args

    def all(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning every unique
        result in priority order.

        Parameters:
            strings: A string or list of strings to translate.
            strings_first: If True, try each string in order with all translators.
                If False, try each translator in order with all strings.

        Returns:
            A list of all unique translated results in priority order.
        """

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Initialize the set of results
        results = []

        # Two options for priority...

        if strings_first:                       # Try each string in order
            for string in strings:
                for translator in self.sequence:
                    partial_results = translator.all(string)
                    if partial_results:
                        for item in partial_results:
                            if item not in results:
                                results.append(item)

        else:                                   # Try each translator in order
            for translator in self.sequence:
                partial_results = translator.all(strings)
                if partial_results:
                    for item in partial_results:
                        if item not in results:
                            results.append(item)

        return results

    def first(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning the first
        result.

        Parameters:
            strings: A string or list of strings to translate.
            strings_first: If True, try each string in order with all translators.
                If False, try each translator in order with all strings.

        Returns:
            The first translated result, or None if no translation is found.
        """

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Two options for priority...

        if strings_first:                       # Try each string in order
            for string in strings:
                for translator in self.sequence:
                    result = translator.first(string)
                    if result is not None:
                        return result

        else:                                   # Try each string in order
            for translator in self.sequence:
                result = translator.first(strings)
                if result is not None:
                    return result

        return None

    def keys(self):
        """Return all of the keys.

        Returns:
            A list of keys from all translators in the sequence.
        """

        key_list = []
        for translator in self.sequence:
            key_list.append(translator.keys())

        return key_list

    def values(self):
        """Return all of the values in the same order as keys().

        Returns:
            A list of values from all translators in the sequence.
        """

        value_list = []
        for translator in self.sequence:
            value_list.append(translator.values())

        return value_list

    def prepend(self, translator):
        """Return a new translator with the given translator in front of this
        one."""

        if translator.TAG == 'NULL':
            return translator

        # If arg is also a sequence, merge
        if translator.TAG == self.TAG:
            return TranslatorBySequence(translator.sequence + self.sequence)

        # If arg matches class of first in sequence, merge
        if translator.TAG == self.sequence[0].TAG:
            new_translator = self.sequence[0].prepend(translator)
            if new_translator.TAG == translator.TAG:
                return TranslatorBySequence(
                    [new_translator] + self.sequence[1:]
                )

        return TranslatorBySequence([translator, self])

    def append(self, translator):
        """Return a new translator with the given translator after this one.
        """

        if translator.TAG == 'NULL':
            return translator

        # If arg is also a sequence, merge
        if translator.TAG == 'SEQUENCE':
            return TranslatorBySequence(self.sequence + translator.sequence)

        # If arg matches class of last in sequence, merge
        if translator.TAG == self.sequence[-1].TAG:
            new_translator = self.sequence[-1].append(translator)
            if new_translator.TAG == translator.TAG:
                return TranslatorBySequence(
                    self.sequence[:-1] + [new_translator]
                )

        return TranslatorBySequence([self, translator])

################################################################################
################################################################################


class TranslatorByDict(Translator):
    """Translator defined by a standard dictionary. Fast but inflexible.

    If the value is string containing "\1", that substring is replaced by the
    key.

    Parameters:
        arg: A dictionary mapping keys to values. Values can be strings (with
            optional "\1" replacement), lists, or tuples.
        path_translator: Optional Translator object that translates input strings
            into the keys used in the dictionary.
    """

    TAG = 'DICT'

    def __init__(self, arg, path_translator=None):
        """Initialize a TranslatorByDict.

        Parameters:
            arg: A dictionary mapping keys to values.
            path_translator: Optional Translator to translate input strings to keys.
        """
        assert isinstance(arg, dict)
        self.dict = arg
        self.path_translator = path_translator

    def all(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning every unique
        result in priority order.

        Parameters:
            strings: A string or list of strings to translate.
            strings_first: Ignored for this subclass.

        Returns:
            A list of all unique translated results in priority order.
        """

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Convert the strings to dictionary keys
        if self.path_translator is None:
            keys = strings
        else:
            keys = self.path_translator.all(strings)

        # Initialize the set of results
        results = []

        # Test keys in order
        for key in keys:
            if key in self.dict:
                result = self.dict[key]
                expanded = TranslatorByDict.expand(result, key)
                for result in expanded:
                    if result not in results:
                        results.append(result)

        return results

    def first(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning the first
        result.

        Parameters:
            strings: A string or list of strings to translate.
            strings_first: Ignored for this subclass.

        Returns:
            The first translated result, or None if no translation is found.
        """

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Convert the strings to dictionary keys, preserving order
        if self.path_translator is None:
            keys = strings
        else:
            keys = self.path_translator.all(strings)

        # Test keys in order
        for key in keys:
            if key in self.dict:
                result = self.dict[key]
                expanded = TranslatorByDict.expand(result, key)
                return expanded[0]

        return None

    @staticmethod
    def expand(results, key):
        """Expand result values by replacing "\1" with the key.

        Parameters:
            results: A value or list of values from the dictionary.
            key: The dictionary key to use for "\1" replacement.

        Returns:
            A list of expanded results.
        """

        if not isinstance(results, list):
            results = [results]

        expanded = []
        for result in results:
            if isinstance(result, str):
                result = result.replace(r'\1', key)
            elif isinstance(result, tuple):
                items = []
                for item in result:
                    if isinstance(item, str):
                        item = item.replace(r'\1', key)
                    items.append(item)
                result = tuple(items)

            expanded.append(result)

        return expanded

    def keys(self):
        """Return all of the keys (in a vaguely sensible order).

        Returns:
            A sorted list of dictionary keys.
        """

        keylist = list(self.dict.keys())
        keylist.sort()
        return keylist

    def values(self):
        """Return all of the values in the same order as keys()."""

        keylist = self.keys()
        return [self.dict[k] for k in keylist]

    def prepend(self, translator):
        """Return a new translator with the given translator in front of this
        one."""

        if translator.TAG == 'NULL':
            return translator

        if translator.TAG == 'SEQUENCE':
            return translator.append(self)

        return TranslatorBySequence([translator, self])

    def append(self, translator):
        """Add a new translator after this one."""

        if translator.TAG == 'NULL':
            return translator

        if translator.TAG == 'SEQUENCE':
            return translator.prepend(self)

        return TranslatorBySequence([self, translator])

################################################################################
################################################################################


class TranslatorByRegex(Translator):
    """Translator defined by a list of tuples defining regular expressions.

    Each element in the list must be a tuple:
        (regular expression string, flags, value)
    or a tuple:
        (compiled regex, value)

    Upon evaluation, if the regular expression matches a given string, using the
    given set of regular expression flags, then the replacement patterns are
    applied to a value and the modified value is returned.

    Parameters:
        tuples: A list of tuples. Each tuple can be:

            - (regex_string, flags, replacement_value) for 3-tuple
            - (regex_string, replacement_value) for 2-tuple
            - (compiled_regex, replacement_value) for 2-tuple with compiled regex

    The replacement value can be a string, a list of strings, or a tuple of
    strings. Strings can contain "#UPPER#", "#LOWER#", "#MIXED#" directives for
    case control, and dictionary expressions like "{'a': 'b'}['a']" for inline
    evaluation.
    """

    TAG = 'REGEX'

    def __init__(self, tuples):
        """Initialize a TranslatorByRegex.

        Parameters:
            tuples: A list of tuples defining regex patterns and replacements.
        """
        # Compile regular expressions (if not already compiled)
        compiled_tuples = []
        for items in tuples:
            if len(items) == 2:
                if isinstance(items[0], str):
                    items = (re.compile('^' + items[0] + '$'), items[1])
                compiled_tuples.append(items)
            else:
                regex = re.compile('^' + items[0] + '$', flags=items[1])
                compiled_tuples.append((regex, items[2]))

        self.tuples = compiled_tuples

    def all(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning every unique
        value in priority order.

        Parameters:
            strings: A string or list of strings to translate.
            strings_first: If True, try each string in order with all regex patterns.
                If False, try each regex pattern in order with all strings.

        Returns:
            A list of all unique translated results in priority order.
        """

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Initialize the list of results
        results = []

        # Two options for priority...
        if strings_first:                       # Try each string in order
            for string in strings:
                for (regex, replacement) in self.tuples:
                    expanded = TranslatorByRegex.expand(
                        regex, string, replacement
                    )
                    for item in expanded:
                        if item not in results:
                            results.append(item)

        else:                                   # Try each regex in order
            for (regex, replacement) in self.tuples:
                for string in strings:
                    expanded = TranslatorByRegex.expand(
                        regex, string, replacement
                    )
                    for item in expanded:
                        if item not in results:
                            results.append(item)

        return results

    def first(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning the first
        result. Return None if no translation is found."""

        # Convert an individual string to a list
        if isinstance(strings, str):
            strings = [strings]

        # Two options for priority...

        if strings_first:                       # Try each string in order
            for string in strings:
                for (regex, replacement) in self.tuples:
                    expanded = TranslatorByRegex.expand(
                        regex, string, replacement
                    )
                    if expanded:
                        return expanded[0]

        else:                                   # Try each regex in order
            for (regex, replacement) in self.tuples:
                for string in strings:
                    expanded = TranslatorByRegex.expand(
                        regex, string, replacement
                    )
                    if expanded:
                        return expanded[0]

        return None

    @staticmethod
    def expand(regex, string, replacements):
        """Handle substitutions in the cases where the replacement is a list, a
        string, or a tuple containing strings.

        Parameters:
            regex: A compiled regular expression pattern.
            string: The string to match against the regex.
            replacements: A string, list of strings, tuple of strings, or other
                value to use as replacement.

        Returns:
            A list of expanded replacement results, or empty list if no match.
        """

        def _fix_case(string):
            # Change text following "#UPPER#" to upper case
            # Change text following "#LOWER#" to lower case
            # Stop changing case of text following "#MIXED#"

            parts = string.split('#')

            newparts = []
            change = 'MIXED'
            literal_hash = False
            for part in parts:
                if part in ('LOWER', 'UPPER', 'MIXED'):
                    change = part
                    literal_hash = False
                else:
                    if change == 'UPPER':
                        part = part.upper()
                    elif change == 'LOWER':
                        part = part.lower()

                    if literal_hash:
                        newparts.append('#')

                    newparts.append(part)
                    literal_hash = True

            return ''.join(newparts)

        def _evaluate_dict(string):
            # Evaluate an in-line dictionary expression

            dicts = re.findall(r'{.*?}\[.*?\]', string)
            for d in dicts:
                value = eval(d)
                string = string.replace(d, value)

            return string

        matchobj = regex.match(string)
        if matchobj is None:
            return []

        if not isinstance(replacements, list):
            replacements = [replacements]

        results = []
        for replacement in replacements:

            # If replacement is a string, apply substitution
            if isinstance(replacement, str):
                result = matchobj.expand(replacement)
                result = _fix_case(result)
                result = _evaluate_dict(result)
                results.append(result)

            # Deal with a tuple
            elif isinstance(replacement, tuple):
                items = []
                for item in replacement:
                    if isinstance(item, str):
                        result = matchobj.expand(item)
                        result = _fix_case(result)
                        result = _evaluate_dict(result)
                        items.append(matchobj.expand(result))
                    else:
                        items.append(item)

                results.append(tuple(items))

            # Anything else is unchanged
            else:
                results.append(replacement)

        return results

    def keys(self):
        """Return all of the keys."""

        return [t[0] for t in self.tuples]

    def values(self):
        """Return all of the values in the same order as keys()."""

        return [t[1] for t in self.tuples]

    def prepend(self, translator):
        """Return a new translator with the given translator in front of this
        one."""

        if translator.TAG == 'NULL':
            return translator

        if translator.TAG == self.TAG:
            return TranslatorByRegex(translator.tuples + self.tuples)

        if translator.TAG == 'SEQUENCE':
            return translator.append(self)

        return TranslatorBySequence([translator, self])

    def append(self, translator):
        """Add a new translator after this one."""

        if translator.TAG == 'NULL':
            return translator

        if translator.TAG == self.TAG:
            return TranslatorByRegex(self.tuples + translator.tuples)

        if translator.TAG == 'SEQUENCE':
            return translator.prepend(self)

        return TranslatorBySequence([self, translator])

################################################################################
################################################################################


class NullTranslator(Translator):
    """Translator that returns nothing."""

    TAG = 'NULL'

    def __init__(self):
        pass

    def all(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning every unique
        result."""

        return []

    def first(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning the first
        result. Return None if no translation is found."""

        return None

    def keys(self):
        """Return all of the keys."""

        return []

    def values(self):
        """Return all of the values in the same order as keys()."""

        return []

    def prepend(self, translator):
        """Return a new translator with the given translator in front of this
        one."""

        return translator

    def append(self, translator):
        """Return a new translator with the given translator after this one.
        """

        return translator

################################################################################
################################################################################


class SelfTranslator(Translator):
    """Translator that returns itself."""

    TAG = 'SELF'

    def __init__(self):
        pass

    def all(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning every unique
        result."""

        return strings

    def first(self, strings, strings_first=False):
        """Apply a translator to one or more strings, returning the first
        result. Return None if no translation is found."""

        return strings[0]

    def keys(self):
        """Return all of the keys."""

        return []

    def values(self):
        """Return all of the values in the same order as keys()."""

        return []

    def prepend(self, translator):
        """Return a new translator with the given translator in front of this
        one."""

        if translator.TAG == self.TAG:
            return self

        if translator.TAG == 'NULL':
            return self

        if translator.TAG == 'SEQUENCE':
            return translator.append(self)

        return TranslatorBySequence([translator, self])

    def append(self, translator):
        """Return a new translator with the given translator after this one.
        """

        if translator.TAG == self.TAG:
            return self

        if translator.TAG == 'NULL':
            return self

        if translator.TAG == 'SEQUENCE':
            return translator.prepend(self)

        return TranslatorBySequence([self, translator])

################################################################################
################################################################################
