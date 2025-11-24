import unittest
import re

from translator import (
    TranslatorByDict,
    TranslatorByRegex,
    TranslatorBySequence,
    NullTranslator,
    SelfTranslator,
)


class TestTranslatorByDict(unittest.TestCase):

    def test_basic_dict_translation(self) -> None:
        trans = TranslatorByDict({
            'apple': 'fruit',
            'carrot': 'vegetable',
            'chicken': 'meat'
        })

        self.assertEqual(trans.first('apple'), 'fruit')
        self.assertEqual(trans.first('carrot'), 'vegetable')
        self.assertIsNone(trans.first('unknown'))

    def test_dict_all_method(self) -> None:
        trans = TranslatorByDict({
            'a': '1',
            'b': '2',
            'c': '3'
        })

        result = trans.all(['a', 'b'])
        self.assertEqual(result, ['1', '2'])

        result = trans.all(['a', 'unknown', 'c'])
        self.assertEqual(result, ['1', '3'])

    def test_dict_with_backslash_one(self) -> None:
        trans = TranslatorByDict({
            'test': 'prefix_\\1_suffix'
        })

        result = trans.first('test')
        self.assertEqual(result, 'prefix_test_suffix')

    def test_dict_with_list_values(self) -> None:
        trans = TranslatorByDict({
            'key': ['value1', 'value2']
        })

        result = trans.all('key')
        self.assertEqual(result, ['value1', 'value2'])


class TestTranslatorByRegex(unittest.TestCase):

    def test_basic_regex_translation(self) -> None:
        trans = TranslatorByRegex([
            (r'data/(\w+)/(\w+)\.txt', r'processed/\1/\2.dat'),
        ])

        result = trans.first('data/2024/observations.txt')
        self.assertEqual(result, 'processed/2024/observations.dat')

        result = trans.first('no_match.txt')
        self.assertIsNone(result)

    def test_regex_with_multiple_patterns(self) -> None:
        trans = TranslatorByRegex([
            (r'images/(\w+)\.jpg', r'thumbnails/\1_thumb.jpg'),
            (r'videos/(\w+)\.mp4', r'clips/\1_clip.mp4'),
        ])

        self.assertEqual(
            trans.first('images/saturn.jpg'),
            'thumbnails/saturn_thumb.jpg'
        )
        self.assertEqual(
            trans.first('videos/jupiter.mp4'),
            'clips/jupiter_clip.mp4'
        )

    def test_regex_all_method(self) -> None:
        trans = TranslatorByRegex([
            (r'file(\d+)', r'output\1'),
        ])

        result = trans.all(['file1', 'file2', 'other'])
        self.assertEqual(result, ['output1', 'output2'])

    def test_regex_with_list_replacements(self) -> None:
        trans = TranslatorByRegex([
            (r'test', [r'result1', r'result2']),
        ])

        result = trans.all('test')
        self.assertEqual(result, ['result1', 'result2'])


class TestTranslatorBySequence(unittest.TestCase):

    def test_sequence_with_dict_and_regex(self) -> None:
        dict_trans = TranslatorByDict({'special': 'handled'})
        regex_trans = TranslatorByRegex([(r'(\w+)', r'default_\1')])

        seq_trans = TranslatorBySequence([dict_trans, regex_trans])

        # Should match dictionary first
        self.assertEqual(seq_trans.first('special'), 'handled')

        # Should fall through to regex
        self.assertEqual(seq_trans.first('other'), 'default_other')

    def test_sequence_all_method(self) -> None:
        trans1 = TranslatorByDict({'a': '1', 'b': '2'})
        trans2 = TranslatorByDict({'c': '3', 'd': '4'})

        seq_trans = TranslatorBySequence([trans1, trans2])

        result = seq_trans.all(['a', 'c', 'unknown'])
        self.assertEqual(result, ['1', '3'])

    def test_sequence_with_strings_first(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'a': '2'})

        seq_trans = TranslatorBySequence([trans1, trans2])

        # Without strings_first, tries each translator on all strings
        result = seq_trans.first(['a', 'b'], strings_first=False)
        self.assertEqual(result, '1')

        # With strings_first, tries all translators on first string
        result = seq_trans.first(['a', 'b'], strings_first=True)
        self.assertEqual(result, '1')

    def test_sequence_prepend(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})

        seq_trans = TranslatorBySequence([trans1])
        new_seq = seq_trans.prepend(trans2)

        self.assertEqual(new_seq.first('b'), '2')
        self.assertEqual(new_seq.first('a'), '1')

    def test_sequence_append(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})

        seq_trans = TranslatorBySequence([trans1])
        new_seq = seq_trans.append(trans2)

        self.assertEqual(new_seq.first('a'), '1')
        self.assertEqual(new_seq.first('b'), '2')


class TestNullTranslator(unittest.TestCase):

    def test_null_returns_nothing(self) -> None:
        trans = NullTranslator()

        self.assertEqual(trans.all('anything'), [])
        self.assertIsNone(trans.first('anything'))
        self.assertEqual(trans.keys(), [])
        self.assertEqual(trans.values(), [])

    def test_null_prepend_and_append(self) -> None:
        null_trans = NullTranslator()
        dict_trans = TranslatorByDict({'a': '1'})

        result = null_trans.prepend(dict_trans)
        self.assertEqual(result.first('a'), '1')

        result = null_trans.append(dict_trans)
        self.assertEqual(result.first('a'), '1')


class TestSelfTranslator(unittest.TestCase):

    def test_self_returns_input(self) -> None:
        trans = SelfTranslator()

        self.assertEqual(trans.all('test'), 'test')
        self.assertEqual(trans.all(['a', 'b']), ['a', 'b'])
        # first() on a string returns first character since strings are iterable
        self.assertEqual(trans.first(['test']), 'test')
        self.assertEqual(trans.first(['a', 'b']), 'a')

    def test_self_keys_and_values(self) -> None:
        trans = SelfTranslator()

        self.assertEqual(trans.keys(), [])
        self.assertEqual(trans.values(), [])

    def test_self_with_sequence(self) -> None:
        self_trans = SelfTranslator()
        dict_trans = TranslatorByDict({'a': '1'})

        seq_trans = TranslatorBySequence([self_trans, dict_trans])

        # Self translator should return input as-is
        self.assertEqual(seq_trans.first('test'), 'test')
        self.assertEqual(seq_trans.first('a'), 'a')


class TestTranslatorOperators(unittest.TestCase):

    def test_add_operator(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})

        combined = trans1 + trans2

        self.assertEqual(combined.first('a'), '1')
        self.assertEqual(combined.first('b'), '2')

    def test_iadd_operator(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})

        trans1 += trans2

        self.assertEqual(trans1.first('a'), '1')
        self.assertEqual(trans1.first('b'), '2')


class TestComplexScenarios(unittest.TestCase):

    def test_nested_sequences(self) -> None:
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        trans3 = TranslatorByDict({'c': '3'})

        seq1 = TranslatorBySequence([trans1, trans2])
        seq2 = TranslatorBySequence([seq1, trans3])

        self.assertEqual(seq2.first('a'), '1')
        self.assertEqual(seq2.first('b'), '2')
        self.assertEqual(seq2.first('c'), '3')

    def test_regex_with_tuple_values(self) -> None:
        trans = TranslatorByRegex([
            (r'file_(\d+)', (r'part1_\1', r'part2_\1')),
        ])

        result = trans.all('file_42')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(result[0], ('part1_42', 'part2_42'))

    def test_dict_with_tuple_values(self) -> None:
        trans = TranslatorByDict({
            'key': ('value1', 'value2')
        })

        result = trans.all('key')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(result[0], ('value1', 'value2'))


class TestTranslatorByDictCoverage(unittest.TestCase):

    def test_dict_with_path_translator(self) -> None:
        """Test TranslatorByDict with a path_translator."""
        path_trans = TranslatorByRegex([(r'input_(\w+)', r'\1')])
        trans = TranslatorByDict({
            'apple': 'fruit',
            'carrot': 'vegetable'
        }, path_translator=path_trans)

        # path_translator converts 'input_apple' to 'apple'
        self.assertEqual(trans.first('input_apple'), 'fruit')
        self.assertEqual(trans.all(['input_apple', 'input_carrot']), ['fruit',
                                                                      'vegetable'])

    def test_dict_expand_with_tuple_and_backslash(self) -> None:
        """Test expand() with tuple values containing \1."""
        trans = TranslatorByDict({
            'key': (r'prefix_\1', r'suffix_\1')
        })

        result = trans.all('key')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(result[0], ('prefix_key', 'suffix_key'))

    def test_dict_expand_with_non_string_tuple_items(self) -> None:
        """Test expand() with tuple containing non-string items."""
        trans = TranslatorByDict({
            'key': (123, 'value')
        })

        result = trans.all('key')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(result[0], (123, 'value'))

    def test_dict_keys_and_values(self) -> None:
        """Test keys() and values() methods."""
        trans = TranslatorByDict({
            'zebra': 'animal',
            'apple': 'fruit',
            'carrot': 'vegetable'
        })

        keys = trans.keys()
        self.assertEqual(keys, ['apple', 'carrot', 'zebra'])

        values = trans.values()
        self.assertEqual(values, ['fruit', 'vegetable', 'animal'])

    def test_dict_prepend_with_sequence(self) -> None:
        """Test prepend() with a SEQUENCE translator."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans2])

        result = trans1.prepend(seq_trans)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_dict_append_with_sequence(self) -> None:
        """Test append() with a SEQUENCE translator."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans2])

        result = trans1.append(seq_trans)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_dict_prepend_with_null(self) -> None:
        """Test prepend() with NULL translator."""
        trans = TranslatorByDict({'a': '1'})
        null_trans = NullTranslator()

        result = trans.prepend(null_trans)
        # NULL translator prepend returns the NULL translator
        self.assertIsInstance(result, NullTranslator)
        self.assertIsNone(result.first('a'))

    def test_dict_append_with_null(self) -> None:
        """Test append() with NULL translator."""
        trans = TranslatorByDict({'a': '1'})
        null_trans = NullTranslator()

        result = trans.append(null_trans)
        # NULL translator append returns the NULL translator
        self.assertIsInstance(result, NullTranslator)
        self.assertIsNone(result.first('a'))


class TestTranslatorBySequenceCoverage(unittest.TestCase):

    def test_sequence_all_with_strings_first_true(self) -> None:
        """Test all() with strings_first=True."""
        trans1 = TranslatorByDict({'a': '1', 'b': '2'})
        trans2 = TranslatorByDict({'a': '3', 'b': '4'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=True, try each string with all translators
        # Order: first string with all translators, then second string with all
        # translators
        result = seq_trans.all(['a', 'b'], strings_first=True)
        # Results are deduplicated, so we get unique values
        self.assertEqual(set(result), {'1', '2', '3', '4'})
        self.assertEqual(len(result), 4)
        # First string 'a' with trans1 gives '1', then 'a' with trans2 gives '3'
        # Then 'b' with trans1 gives '2', then 'b' with trans2 gives '4'
        # So order should be: '1', '3', '2', '4'
        self.assertEqual(result[:2], ['1', '3'])  # First string results

    def test_sequence_all_with_single_string(self) -> None:
        """Test all() with a single string input."""
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])

        result = seq_trans.all('a')
        self.assertEqual(result, ['1'])

    def test_sequence_first_with_strings_first_true(self) -> None:
        """Test first() with strings_first=True."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=True, try first string with all translators
        result = seq_trans.first(['a', 'b'], strings_first=True)
        self.assertEqual(result, '1')

    def test_sequence_first_with_single_string(self) -> None:
        """Test first() with a single string input."""
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])

        result = seq_trans.first('a')
        self.assertEqual(result, '1')

    def test_sequence_keys_and_values(self) -> None:
        """Test keys() and values() methods."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        keys = seq_trans.keys()
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0], ['a'])
        self.assertEqual(keys[1], ['b'])

        values = seq_trans.values()
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0], ['1'])
        self.assertEqual(values[1], ['2'])

    def test_sequence_prepend_with_null(self) -> None:
        """Test prepend() with NULL translator."""
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])
        null_trans = NullTranslator()

        result = seq_trans.prepend(null_trans)
        self.assertIsInstance(result, NullTranslator)

    def test_sequence_prepend_with_same_tag(self) -> None:
        """Test prepend() with another SEQUENCE translator."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq1 = TranslatorBySequence([trans1])
        seq2 = TranslatorBySequence([trans2])

        result = seq1.prepend(seq2)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_sequence_prepend_with_matching_first_tag(self) -> None:
        """Test prepend() when translator matches first in sequence."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        result = seq_trans.prepend(trans2)
        # Should merge dict translators
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_sequence_append_with_null(self) -> None:
        """Test append() with NULL translator."""
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])
        null_trans = NullTranslator()

        result = seq_trans.append(null_trans)
        self.assertIsInstance(result, NullTranslator)

    def test_sequence_append_with_same_tag(self) -> None:
        """Test append() with another SEQUENCE translator."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq1 = TranslatorBySequence([trans1])
        seq2 = TranslatorBySequence([trans2])

        result = seq1.append(seq2)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_sequence_append_with_matching_last_tag(self) -> None:
        """Test append() when translator matches last in sequence."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        result = seq_trans.append(trans2)
        # Should merge dict translators
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')


class TestTranslatorByRegexCoverage(unittest.TestCase):

    def test_regex_init_with_2_tuple_string(self) -> None:
        """Test __init__ with 2-tuple containing string regex."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1')
        ])

        result = trans.first('test')
        self.assertEqual(result, 'prefix_test')

    def test_regex_init_with_2_tuple_compiled(self) -> None:
        """Test __init__ with 2-tuple containing compiled regex."""
        compiled_regex = re.compile(r'^(\w+)$')
        trans = TranslatorByRegex([
            (compiled_regex, r'prefix_\1')
        ])

        result = trans.first('test')
        self.assertEqual(result, 'prefix_test')

    def test_regex_init_with_3_tuple(self) -> None:
        """Test __init__ with 3-tuple (regex, flags, replacement)."""
        trans = TranslatorByRegex([
            (r'(\w+)', re.IGNORECASE, r'prefix_\1')
        ])

        result = trans.first('TEST')
        self.assertEqual(result, 'prefix_TEST')

    def test_regex_all_with_strings_first_true(self) -> None:
        """Test all() with strings_first=True."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1'),
            (r'(\d+)', r'number_\1')
        ])

        result = trans.all(['test', '123'], strings_first=True)
        # With strings_first=True: try 'test' with all patterns, then '123' with
        # all patterns
        # 'test' matches (\w+) -> 'prefix_test', doesn't match (\d+)
        # '123' matches (\w+) -> 'prefix_123', matches (\d+) -> 'number_123'
        # Results are deduplicated
        self.assertEqual(set(result), {'prefix_test', 'prefix_123', 'number_123'})
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 'prefix_test')  # First string, first pattern

    def test_regex_all_with_single_string(self) -> None:
        """Test all() with a single string input."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1')
        ])

        result = trans.all('test')
        self.assertEqual(result, ['prefix_test'])

    def test_regex_first_with_strings_first_true(self) -> None:
        """Test first() with strings_first=True."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1'),
            (r'(\d+)', r'number_\1')
        ])

        result = trans.first(['test', '123'], strings_first=True)
        self.assertEqual(result, 'prefix_test')

    def test_regex_first_with_single_string(self) -> None:
        """Test first() with a single string input."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1')
        ])

        result = trans.first('test')
        self.assertEqual(result, 'prefix_test')

    def test_regex_expand_with_upper_case(self) -> None:
        """Test expand() with #UPPER# directive."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', r'#UPPER#\1')
        self.assertEqual(result, ['TEST'])

    def test_regex_expand_with_lower_case(self) -> None:
        """Test expand() with #LOWER# directive."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'TEST', r'#LOWER#\1')
        self.assertEqual(result, ['test'])

    def test_regex_expand_with_mixed_case(self) -> None:
        """Test expand() with #MIXED# directive."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'Test', r'#MIXED#\1')
        self.assertEqual(result, ['Test'])

    def test_regex_expand_with_case_switching(self) -> None:
        """Test expand() with multiple case directives."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', r'#UPPER#\1#LOWER#_suffix')
        self.assertEqual(result, ['TEST_suffix'])

    def test_regex_expand_with_literal_hash(self) -> None:
        """Test expand() with literal # characters."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', r'prefix#\1#suffix')
        self.assertEqual(result, ['prefix#test#suffix'])

    def test_regex_expand_with_dict_evaluation(self) -> None:
        """Test expand() with dictionary expression evaluation."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', r'prefix_{"a": "b"}["a"]_suffix')
        self.assertEqual(result, ['prefix_b_suffix'])

    def test_regex_expand_with_tuple_replacement(self) -> None:
        """Test expand() with tuple replacement containing non-strings."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', (123, r'\1'))
        self.assertEqual(result, [(123, 'test')])

    def test_regex_expand_with_non_string_replacement(self) -> None:
        """Test expand() with non-string replacement."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', 123)
        self.assertEqual(result, [123])

    def test_regex_expand_no_match(self) -> None:
        """Test expand() when regex doesn't match."""
        regex = re.compile(r'^(\d+)$')
        result = TranslatorByRegex.expand(regex, 'test', r'\1')
        self.assertEqual(result, [])

    def test_regex_keys_and_values(self) -> None:
        """Test keys() and values() methods."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1'),
            (r'(\d+)', r'number_\1')
        ])

        keys = trans.keys()
        self.assertEqual(len(keys), 2)
        self.assertTrue(all(isinstance(k, type(re.compile(''))) for k in keys))

        values = trans.values()
        self.assertEqual(values, [r'prefix_\1', r'number_\1'])

    def test_regex_prepend_with_null(self) -> None:
        """Test prepend() with NULL translator."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        null_trans = NullTranslator()

        result = trans.prepend(null_trans)
        self.assertIsInstance(result, NullTranslator)

    def test_regex_prepend_with_same_tag(self) -> None:
        """Test prepend() with another REGEX translator."""
        trans1 = TranslatorByRegex([(r'a', r'1')])
        trans2 = TranslatorByRegex([(r'b', r'2')])

        result = trans1.prepend(trans2)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_regex_prepend_with_sequence(self) -> None:
        """Test prepend() with SEQUENCE translator."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        seq_trans = TranslatorBySequence([TranslatorByDict({'a': '1'})])

        result = trans.prepend(seq_trans)
        self.assertEqual(result.first('a'), '1')

    def test_regex_append_with_null(self) -> None:
        """Test append() with NULL translator."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        null_trans = NullTranslator()

        result = trans.append(null_trans)
        self.assertIsInstance(result, NullTranslator)

    def test_regex_append_with_same_tag(self) -> None:
        """Test append() with another REGEX translator."""
        trans1 = TranslatorByRegex([(r'a', r'1')])
        trans2 = TranslatorByRegex([(r'b', r'2')])

        result = trans1.append(trans2)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_regex_append_with_sequence(self) -> None:
        """Test append() with SEQUENCE translator."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        seq_trans = TranslatorBySequence([TranslatorByDict({'a': '1'})])

        result = trans.append(seq_trans)
        # When regex is appended to sequence, sequence.prepend is called
        # This creates TranslatorBySequence([regex, dict_trans])
        # So regex is tried first, which matches 'a' -> 'a'
        self.assertEqual(result.first('a'), 'a')  # regex matches first
        self.assertEqual(result.first('b'), 'b')  # regex matches


class TestSelfTranslatorCoverage(unittest.TestCase):

    def test_self_first_with_single_string(self) -> None:
        """Test first() with a single string."""
        trans = SelfTranslator()
        result = trans.first('test')
        self.assertEqual(result, 't')  # strings[0] of 'test' is 't'

    def test_self_prepend_with_self_tag(self) -> None:
        """Test prepend() with another SELF translator."""
        self1 = SelfTranslator()
        self2 = SelfTranslator()

        result = self1.prepend(self2)
        self.assertIsInstance(result, SelfTranslator)

    def test_self_prepend_with_null(self) -> None:
        """Test prepend() with NULL translator."""
        self_trans = SelfTranslator()
        null_trans = NullTranslator()

        result = self_trans.prepend(null_trans)
        self.assertIsInstance(result, SelfTranslator)

    def test_self_prepend_with_sequence(self) -> None:
        """Test prepend() with SEQUENCE translator."""
        self_trans = SelfTranslator()
        seq_trans = TranslatorBySequence([TranslatorByDict({'a': '1'})])

        result = self_trans.prepend(seq_trans)
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('test'), 'test')

    def test_self_append_with_self_tag(self) -> None:
        """Test append() with another SELF translator."""
        self1 = SelfTranslator()
        self2 = SelfTranslator()

        result = self1.append(self2)
        self.assertIsInstance(result, SelfTranslator)

    def test_self_append_with_null(self) -> None:
        """Test append() with NULL translator."""
        self_trans = SelfTranslator()
        null_trans = NullTranslator()

        result = self_trans.append(null_trans)
        self.assertIsInstance(result, SelfTranslator)

    def test_self_append_with_sequence(self) -> None:
        """Test append() with SEQUENCE translator."""
        self_trans = SelfTranslator()
        seq_trans = TranslatorBySequence([TranslatorByDict({'a': '1'})])

        result = self_trans.append(seq_trans)
        # SelfTranslator returns input first, so 'test' -> 'test'
        self.assertEqual(result.first('test'), 'test')
        # But 'a' also matches self first, so returns 'a' not '1'
        # This is because SelfTranslator is first in the sequence
        self.assertEqual(result.first('a'), 'a')


class TestVersionImport(unittest.TestCase):

    def test_version_import_fallback(self) -> None:
        """Test that version import fallback works."""
        # This tests the ImportError handling in __init__.py
        # We can't easily test the actual import error, but we can verify
        # that __version__ exists
        from translator import __version__
        self.assertIsNotNone(__version__)
        self.assertIsInstance(__version__, str)


class TestEdgeCasesCoverage(unittest.TestCase):

    def test_sequence_all_with_empty_results(self) -> None:
        """Test all() when translators return empty results."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = NullTranslator()  # Returns empty
        seq_trans = TranslatorBySequence([trans1, trans2])

        # trans2 returns empty, so should not add to results
        result = seq_trans.all(['a'], strings_first=True)
        self.assertEqual(result, ['1'])

        result = seq_trans.all(['a'], strings_first=False)
        self.assertEqual(result, ['1'])

    def test_sequence_all_with_duplicate_results(self) -> None:
        """Test all() when results contain duplicates."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'a': '1'})  # Same result
        seq_trans = TranslatorBySequence([trans1, trans2])

        # Should deduplicate
        result = seq_trans.all(['a'], strings_first=True)
        self.assertEqual(result, ['1'])

    def test_sequence_prepend_tag_mismatch(self) -> None:
        """Test prepend() when merged translator has different TAG."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        # When prepending, if the merged result has different TAG,
        # it should create a new sequence
        result = seq_trans.prepend(trans2)
        # The prepend should merge dicts, but if TAG doesn't match,
        # it creates a sequence
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_sequence_append_tag_match(self) -> None:
        """Test append() when merged translator has same TAG."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        # When appending same TAG translator, should merge
        result = seq_trans.append(trans2)
        # Should merge into a sequence since prepend/append on dict creates sequence
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_dict_expand_with_non_string_non_tuple(self) -> None:
        """Test expand() with non-string, non-tuple result."""
        # Test with integer value
        trans = TranslatorByDict({'key': 123})
        result = trans.all('key')
        self.assertEqual(result, [123])

    def test_regex_init_with_2_tuple_compiled_regex(self) -> None:
        """Test __init__ with 2-tuple containing compiled regex (not string)."""
        compiled_regex = re.compile(r'^(\w+)$')
        trans = TranslatorByRegex([
            (compiled_regex, r'prefix_\1')
        ])

        result = trans.first('test')
        self.assertEqual(result, 'prefix_test')

    def test_regex_expand_tuple_with_non_string_items(self) -> None:
        """Test expand() with tuple containing non-string items."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', (123, 456))
        self.assertEqual(result, [(123, 456)])

    def test_regex_expand_tuple_with_mixed_items(self) -> None:
        """Test expand() with tuple containing both string and non-string items."""
        regex = re.compile(r'^(\w+)$')
        result = TranslatorByRegex.expand(regex, 'test', (r'\1', 123))
        self.assertEqual(result, [('test', 123)])

    def test_regex_expand_tuple_string_with_dict_eval(self) -> None:
        """Test expand() with tuple string item that needs dict evaluation."""
        regex = re.compile(r'^(\w+)$')
        # Tuple with string that has dict expression
        result = TranslatorByRegex.expand(regex, 'test',
                                          (r'prefix_{"a": "b"}["a"]', r'\1'))
        # The dict evaluation happens, then it's expanded again (line 464)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        # The first item should have dict evaluated
        self.assertEqual(result[0][0], 'prefix_b')
        self.assertEqual(result[0][1], 'test')

    def test_sequence_all_duplicate_check_false_branch(self) -> None:
        """Test all() duplicate check when strings_first=False."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'a': '1'})  # Same result
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=False, should deduplicate
        result = seq_trans.all(['a'], strings_first=False)
        self.assertEqual(result, ['1'])

    def test_sequence_first_none_branch(self) -> None:
        """Test first() when translator returns None."""
        trans1 = NullTranslator()  # Returns None
        trans2 = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # trans1 returns None, should continue to trans2
        result = seq_trans.first('a', strings_first=True)
        self.assertEqual(result, '1')

        result = seq_trans.first('a', strings_first=False)
        self.assertEqual(result, '1')

    def test_sequence_prepend_tag_match_branch(self) -> None:
        """Test prepend() when merged translator TAG matches."""
        # Create a scenario where prepend merges and TAG matches
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        # When prepending a dict to a sequence starting with dict,
        # it should try to merge
        result = seq_trans.prepend(trans2)
        # The merge creates a sequence, not a dict, so TAG won't match
        # But we can test the branch by checking the behavior
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_sequence_append_tag_match_branch(self) -> None:
        """Test append() when merged translator TAG matches."""
        trans1 = TranslatorByDict({'a': '1'})
        trans2 = TranslatorByDict({'b': '2'})
        seq_trans = TranslatorBySequence([trans1])

        # When appending a dict to a sequence ending with dict,
        # it should try to merge
        result = seq_trans.append(trans2)
        # The merge creates a sequence, not a dict, so TAG won't match
        # But we can test the branch by checking the behavior
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')

    def test_dict_all_duplicate_check(self) -> None:
        """Test all() duplicate check in TranslatorByDict."""
        trans = TranslatorByDict({
            'a': ['1', '1']  # List with duplicate
        })

        result = trans.all('a')
        self.assertEqual(result, ['1'])  # Should deduplicate

    def test_regex_all_duplicate_check_strings_first_true(self) -> None:
        """Test all() duplicate check when strings_first=True."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1'),
            (r'(\w+)', r'prefix_\1')  # Same pattern, same result
        ])

        result = trans.all(['test'], strings_first=True)
        self.assertEqual(result, ['prefix_test'])  # Should deduplicate

    def test_regex_all_duplicate_check_strings_first_false(self) -> None:
        """Test all() duplicate check when strings_first=False."""
        trans = TranslatorByRegex([
            (r'(\w+)', r'prefix_\1'),
            (r'(\w+)', r'prefix_\1')  # Same pattern, same result
        ])

        result = trans.all(['test'], strings_first=False)
        self.assertEqual(result, ['prefix_test'])  # Should deduplicate

    def test_regex_first_empty_expanded_strings_first_true(self) -> None:
        """Test first() when expanded is empty with strings_first=True."""
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits (full match)
            (r'^(\w+)$', r'word_\1')      # Matches words (full match)
        ])

        # First pattern doesn't match 'test', expanded is empty
        # Should continue to second pattern
        result = trans.first('test', strings_first=True)
        self.assertEqual(result, 'word_test')

    def test_regex_first_empty_expanded_strings_first_false(self) -> None:
        """Test first() when expanded is empty with strings_first=False."""
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits (full match)
            (r'^(\w+)$', r'word_\1')      # Matches words (full match)
        ])

        # First pattern doesn't match 'test', expanded is empty
        # Should continue to second pattern
        result = trans.first('test', strings_first=False)
        self.assertEqual(result, 'word_test')

    def test_regex_prepend_final_return(self) -> None:
        """Test prepend() final return branch."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        dict_trans = TranslatorByDict({'a': '1'})

        # When prepending dict (not NULL, not REGEX, not SEQUENCE)
        result = trans.prepend(dict_trans)
        self.assertIsInstance(result, TranslatorBySequence)
        self.assertEqual(result.first('a'), '1')

    def test_regex_append_final_return(self) -> None:
        """Test append() final return branch."""
        trans = TranslatorByRegex([(r'(\w+)', r'\1')])
        dict_trans = TranslatorByDict({'a': '1'})

        # When appending dict (not NULL, not REGEX, not SEQUENCE)
        result = trans.append(dict_trans)
        self.assertIsInstance(result, TranslatorBySequence)
        # Sequence has regex first, then dict, so 'a' matches regex first -> 'a'
        self.assertEqual(result.first('a'), 'a')
        # But 'b' (not in dict) matches regex -> 'b'
        self.assertEqual(result.first('b'), 'b')

    def test_self_prepend_final_return(self) -> None:
        """Test prepend() final return branch."""
        self_trans = SelfTranslator()
        dict_trans = TranslatorByDict({'a': '1'})

        # When prepending dict (not SELF, not NULL, not SEQUENCE)
        result = self_trans.prepend(dict_trans)
        self.assertIsInstance(result, TranslatorBySequence)
        self.assertEqual(result.first('a'), '1')

    def test_self_append_final_return(self) -> None:
        """Test append() final return branch."""
        self_trans = SelfTranslator()
        dict_trans = TranslatorByDict({'a': '1'})

        # When appending dict (not SELF, not NULL, not SEQUENCE)
        result = self_trans.append(dict_trans)
        self.assertIsInstance(result, TranslatorBySequence)
        # Sequence has self first, then dict, so 'a' matches self first -> 'a'
        self.assertEqual(result.first('a'), 'a')
        # But 'b' (not in dict) matches self -> 'b'
        self.assertEqual(result.first('b'), 'b')

    def test_sequence_first_none_continues_strings_first_true(self) -> None:
        """Test first() continues when result is None with strings_first=True."""
        trans1 = NullTranslator()  # Returns None
        trans2 = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=True, trans1 returns None, should continue to trans2
        result = seq_trans.first('a', strings_first=True)
        self.assertEqual(result, '1')

    def test_sequence_prepend_tag_match_branch_regex(self) -> None:
        """Test prepend() when merged translator TAG matches (regex case)."""
        trans1 = TranslatorByRegex([(r'a', r'1')])
        trans2 = TranslatorByRegex([(r'b', r'2')])
        seq_trans = TranslatorBySequence([trans1])

        # When prepending a regex to a sequence starting with regex,
        # prepend merges them and TAG matches, so creates sequence with merged regex
        result = seq_trans.prepend(trans2)
        # Should merge into a sequence with the merged regex
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')
        # The branch at line 197 is taken when TAG matches
        # It creates a sequence with the merged translator
        self.assertIsInstance(result, TranslatorBySequence)
        # Verify the merged regex is in the sequence
        self.assertEqual(len(result.sequence), 1)
        self.assertEqual(result.sequence[0].TAG, 'REGEX')

    def test_sequence_append_tag_match_branch_regex(self) -> None:
        """Test append() when merged translator TAG matches (regex case)."""
        trans1 = TranslatorByRegex([(r'a', r'1')])
        trans2 = TranslatorByRegex([(r'b', r'2')])
        seq_trans = TranslatorBySequence([trans1])

        # When appending a regex to a sequence ending with regex,
        # append merges them and TAG matches, so creates sequence with merged regex
        result = seq_trans.append(trans2)
        # Should merge into a sequence with the merged regex
        self.assertEqual(result.first('a'), '1')
        self.assertEqual(result.first('b'), '2')
        # The branch at line 216 is taken when TAG matches
        # It creates a sequence with the merged translator
        self.assertIsInstance(result, TranslatorBySequence)
        # Verify the merged regex is in the sequence
        self.assertEqual(len(result.sequence), 1)
        self.assertEqual(result.sequence[0].TAG, 'REGEX')

    def test_regex_first_empty_expanded_continues_strings_first_true(self) -> None:
        """Test first() continues when expanded is empty with strings_first=True."""
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits
            (r'^(\w+)$', r'word_\1')      # Matches words
        ])

        # First pattern doesn't match 'test', expanded is empty, should continue
        result = trans.first('test', strings_first=True)
        self.assertEqual(result, 'word_test')

    def test_regex_first_empty_expanded_continues_strings_first_false(self) -> None:
        """Test first() continues when expanded is empty with strings_first=False."""
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits
            (r'^(\w+)$', r'word_\1')      # Matches words
        ])

        # First pattern doesn't match 'test', expanded is empty, should continue
        result = trans.first('test', strings_first=False)
        self.assertEqual(result, 'word_test')

    def test_sequence_first_none_continues_strings_first_false_explicit(self) -> None:
        """Test first() with strings_first=False when first translator returns None."""
        # Explicitly test the else branch (strings_first=False)
        trans1 = NullTranslator()  # Returns None
        trans2 = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=False (default), should try trans1 first (returns None),
        # then continue to trans2
        result = seq_trans.first(['a'], strings_first=False)
        self.assertEqual(result, '1')

    def test_sequence_first_none_continues_strings_first_true_explicit(self) -> None:
        """Test first() with strings_first=True when translator returns None."""
        # Explicitly test the if branch (strings_first=True) with None result
        trans1 = NullTranslator()  # Returns None
        trans2 = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans1, trans2])

        # With strings_first=True, should try first string with trans1 (None),
        # then continue to trans2
        result = seq_trans.first(['a'], strings_first=True)
        self.assertEqual(result, '1')

    def test_regex_first_empty_expanded_continues_strings_first_false_explicit(self
                                                                               ) -> None:
        """Test first() with strings_first=False when expanded is empty."""
        # Explicitly test the else branch
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits
            (r'^(\w+)$', r'word_\1')      # Matches words
        ])

        # With strings_first=False, first regex doesn't match, expanded is empty,
        # should continue to second regex
        result = trans.first(['test'], strings_first=False)
        self.assertEqual(result, 'word_test')

    def test_regex_first_empty_expanded_continues_strings_first_true_explicit(self
                                                                              ) -> None:
        """Test first() with strings_first=True when expanded is empty."""
        # Explicitly test the if branch
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1'),  # Only matches digits
            (r'^(\w+)$', r'word_\1')      # Matches words
        ])

        # With strings_first=True, first regex doesn't match first string,
        # expanded is empty, should continue to second regex
        result = trans.first(['test'], strings_first=True)
        self.assertEqual(result, 'word_test')

    def test_sequence_first_empty_list_strings_first_true(self) -> None:
        """Test first() with empty list and strings_first=True to cover branch 145->155.
        """
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])

        # Empty list with strings_first=True: the for loop at line 145 doesn't execute,
        # so it falls through to line 155 (return None)
        # This covers the branch 145->155 (from if block to return None)
        result = seq_trans.first([], strings_first=True)
        self.assertIsNone(result)

    def test_sequence_first_empty_list_strings_first_false(self) -> None:
        """Test first() with empty list and strings_first=False to cover branch 145->155.
        """
        trans = TranslatorByDict({'a': '1'})
        seq_trans = TranslatorBySequence([trans])

        # Empty list with strings_first=False: goes to else block, for loop doesn't
        # execute, goes to return None at line 155
        result = seq_trans.first([], strings_first=False)
        self.assertIsNone(result)

    def test_regex_first_empty_list_strings_first_true(self) -> None:
        """Test first() with empty list and strings_first=True to cover branch 486->501.
        """
        trans = TranslatorByRegex([
            (r'^(\w+)$', r'prefix_\1')
        ])

        # Empty list with strings_first=True: the for loop at line 486 doesn't execute,
        # so it falls through to line 501 (return None)
        # This covers the branch 486->501 (from if block to return None)
        result = trans.first([], strings_first=True)
        self.assertIsNone(result)

    def test_regex_first_empty_list_strings_first_false(self) -> None:
        """Test first() with empty list and strings_first=False to cover branch 486->501.
        """
        trans = TranslatorByRegex([
            (r'^(\w+)$', r'prefix_\1')
        ])

        # Empty list with strings_first=False: goes to else block, for loop doesn't
        # execute, goes to return None at line 501
        result = trans.first([], strings_first=False)
        self.assertIsNone(result)

    def test_sequence_first_inner_loop_continues_strings_first_true(self) -> None:
        """Test first() with strings_first=True where inner loop completes and continues.

        This covers branch 146->145: when the inner translator loop completes without
        finding a result, it continues to the next string in the outer loop.
        """
        trans = TranslatorByDict({'b': '2'})  # Only matches 'b', not 'a'
        seq_trans = TranslatorBySequence([trans])

        # With strings_first=True: try 'a' with trans (no match), inner loop completes,
        # continue to next string 'b' (matches)
        result = seq_trans.first(['a', 'b'], strings_first=True)
        self.assertEqual(result, '2')

    def test_regex_first_inner_loop_continues_strings_first_true(self) -> None:
        """Test first() with strings_first=True where inner loop completes and continues.

        This covers branch 487->486: when the inner regex loop completes without
        finding a match, it continues to the next string in the outer loop.
        """
        trans = TranslatorByRegex([
            (r'^(\d+)$', r'number_\1')  # Only matches digits
        ])

        # With strings_first=True: try 'test' with regex (no match), inner loop completes,
        # continue to next string '123' (matches)
        result = trans.first(['test', '123'], strings_first=True)
        self.assertEqual(result, 'number_123')


if __name__ == '__main__':
    unittest.main()
