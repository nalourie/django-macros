from django.test import TestCase
from django import template
from django.template import Template, Context
from django.shortcuts import render_to_response

# Parser creation factory for testing
import django.template.base as template_base

def make_parser(template_string):
    return template_base.Parser(
        template_base.Lexer(
            template_string,
            template_base.StringOrigin(template_string)).tokenize())


# Tests for repeatedblocks.py
from .templatetags.repeatedblocks import set_repeated_blocks, BlockNode

class RepeatedBlocksTagsTests(TestCase):

    # generate test templates from these base
    # strings to be more dry/in case tag syntax
    # changes later.
    LOAD_STRING = "{% load repeatedblocks %}"
    # define first repeated_block strings
    RBLOCK_1_NAME = "rblock1"
    DEFINE_RBLOCK_1 = (
            "{% repeated_block {0} %}".format(RBLOCK_1_NAME) + 
                "string1"
            "{% endblock %}")
    REPEAT_RBLOCK_1 = "{% repeat {0} %}".format(RBLOCK_1_NAME)
    # define second repeated_block strings
    RBLOCK_2_NAME = "rblock2"
    DEFINE_RBLOCK_2 = (
            "{% repeated_block {0} %}".format(RBLOCK_2_NAME) + 
                "string2"
            "{% endblock %}")
    REPEAT_RBLOCK_2 = "{% repeat {0} %}".format(RBLOCK_2_NAME)
    # too few and too many args
    TOO_FEW_REPEATED_BLOCK = "{% repeated_block %}"
    TOO_MANY_REPEATED_BLOCK = "{% repeated_block arg1 arg2 %}"
    TOO_FEW_REPEAT = "{% repeat %}"
    TOO_MANY_REPEAT = "{% repeat arg1 arg2 %}"
    
    # test assumptions
    def test_creates_normal_block(self):
        """ It is assumed that the block node created
        by the repeated block tag, and the block node
        created by the usual block tag are identical.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1)
        # assert that there is only one node in template
        self.assertEqual(len(t.nodelist), 1)
        # make sure that node is a block node
        self.assertIsInstance(t.nodelist[0], BlockNode)
        # make sure that node is the block node we expect it to be
        self.assertEqual(t.nodelist[0].name, self.RBLOCK_1_NAME)

    # test functionality

    ## test set_repeated_blocks
    def test_set_repeated_blocks_sets_variable(self):
        """ Set repeated blocks must set the _repeated_blocks
        variable on the parser.
        """
        p = make_parser("A short template")
        # check that the parser doesn't initially have the
        # _repeated_blocks attribute
        self.assertFalse(hasattr(p, "_repeated_blocks"))
        # check that set_repeated_blocks actually sets the
        # attribute.
        set_repeated_blocks(p)
        self.assertTrue(hasattr(p, "_repeated_blocks"))

    def test_set_repeated_blocks_doesnt_overwrite(self):
        """ Set repeated blocks must not overwrite the
        _repeated_blocks variable on the parser, if it
        already exists.
        """
        p = make_parser("A short template")
        # set the attribute to a specific dict
        dic = {'foo': 'bar', }
        p._repeated_blocks = dic
        # call set_repeated_blocks and test that
        # the dict hasn't been overwritten.
        set_repeated_blocks(p)
        self.assertEqual(p._repeated_blocks, dic)

    def test_set_repeated_blocks_initialize_empty(self):
        """ Set repeated blocks must initialize the
        the _repeated_blocks variable as an empty dict.
        """
        p = make_parser("A short template")
        set_repeated_blocks(p)
        self.assertEqual(p._repeated_blocks, {})

    ## test repeated_block and repeat
    def test_repeated_block_repeats_once(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats once.
        """
        t = Template(
            LOAD_STRING + DEFINE_RBLOCK_1 +
            REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1")
        

    def test_repeated_block_repeats_twice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats twice.
        """
        t = Template(
            LOAD_STRING + DEFINE_RBLOCK_1 +
            REPEAT_RBLOCK_1 +
            REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1string1")

    def test_repeated_block_repeats_thrice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats thrice.
        """
        t = Template(
            LOAD_STRING + DEFINE_RBLOCK_1 +
            REPEAT_RBLOCK_1 +
            REPEAT_RBLOCK_1 +
            REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string1")

    def test_two_distinct_repeat_blocks(self):
        """ Multiple repeated blocks should be able to
        exist and work at the same time.
        """
        t = Template(
            LOAD_STRING + DEFINE_RBLOCK_1 +
            REPEAT_RBLOCK_1 +
            DEFINE_RBLOCK_2 +
            REPEAT_RBLOCK_1 +
            REPEAT_RBLOCK_2 +
            REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string2string1")

    # test exceptions
    def test_repeat_coming_before_repeated_block(self):
        """ If the repeat tag comes before the repeated
        block tag, it should throw an exception.
        """
        t = Template(
            LOAD_STRING + REPEAT_RBLOCK_1 +
            DEFINE_RBLOCK_1)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            t.render,
            c)
    
    def test_repeat_having_no_block(self):
        """ If repeat is called without a repeated block
        definition existing, than repeat should throw an
        exception.
        """
        t = Template(
            LOAD_STRING + REPEAT_RBLOCK_2)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            t.render,
            c)

    def test_repeat_having_no_block_of_same_name(self):
        """ If repeat is called without a repeated block of
        the corresponding name existing, than repeat should
        throw an exception.
        """
        t = Template(
            LOAD_STRING + DEFINE_RBLOCK_1 +
            REPEAT_RBLOCK_2)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block {0} tag was found before the .+ tag$".format(
                RBLOCK_2_NAME),
            t.render,
            c)

    def test_repeated_block_with_no_args(self):
        """ repeated_block should throw an exception when
        called without arguments.
        """
        t = Template(
            LOAD_STRING + TOO_FEW_REPEATED_BLOCK)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            t.render,
            c)
    
    def test_repeated_block_with_too_many_args(self):
        """ repeated_block should throw an exception when
        called with too many arguments.
        """
        t = Template(
            LOAD_STRING + TOO_MANY_REPEATED_BLOCK)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            t.render,
            c)

    def test_repeat_with_no_args(self):
        """ repeat should throw an exception when
        called without arguments.
        """
        t = Template(
            LOAD_STRING + TOO_FEW_REPEAT)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            t.render,
            c)
    
    def test_repeat_with_too_many_args(self):
        """ repeat should throw an exception when
        called with too many arguments.
        """
        t = Template(
            LOAD_STRING + TOO_MANY_REPEAT)
        c = Context({})
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            t.render,
            c)



    
class MacrosTests(TestCase):

    # test assumptions
        ## no obvious assumptions made about implementation.
    
    # test functionality

    ## test _setup_macros_dict
    def test_set__setup_macros_dict_sets_variable(self):
        """ Set repeated blocks must set the _repeated_blocks
        variable on the parser.
        """
        pass

    def test_set__setup_macros_dict_doesnt_overwrite(self):
        """ Set repeated blocks must not overwrite the
        _repeated_blocks variable on the parser, if it
        already exists.
        """
        pass

    def test_set__setup_macros_dict_initialize_empty(self):
        """ Set repeated blocks must initialize the
        the _repeated_blocks variable as an empty dict.
        """
        pass

    ## test load macros

    ## test macro, use_macro, and macro_block

    
    # test exceptions

