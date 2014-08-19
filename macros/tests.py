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
            "{{% repeated_block {0} %}}".format(RBLOCK_1_NAME) + 
                "string1"
            "{% endblock %}")
    REPEAT_RBLOCK_1 = "{{% repeat {0} %}}".format(RBLOCK_1_NAME)
    # define second repeated_block strings
    RBLOCK_2_NAME = "rblock2"
    DEFINE_RBLOCK_2 = (
            "{{% repeated_block {0} %}}".format(RBLOCK_2_NAME) + 
                "string2"
            "{% endblock %}")
    REPEAT_RBLOCK_2 = "{{% repeat {0} %}}".format(RBLOCK_2_NAME)
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
        # assert that there is only two nodes in template
            # first node is the load tag
            # second node is the block node
        self.assertEqual(len(t.nodelist), 2)
        # make sure that the second node is a block node
        self.assertIsInstance(t.nodelist[1], BlockNode)
        # make sure that node is the block node we expect it to be
        self.assertEqual(t.nodelist[1].name, self.RBLOCK_1_NAME)

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
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1string1")
        

    def test_repeated_block_repeats_twice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats twice.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1string1string1")

    def test_repeated_block_repeats_thrice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats thrice.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string1string1")

    def test_two_distinct_repeat_blocks(self):
        """ Multiple repeated blocks should be able to
        exist and work at the same time.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.DEFINE_RBLOCK_2 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_2 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string2string1string2string1")

    # test exceptions
    def test_repeat_coming_before_repeated_block(self):
        """ If the repeat tag comes before the repeated
        block tag, it should throw an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.REPEAT_RBLOCK_1 +
            self.DEFINE_RBLOCK_1,)
    
    def test_repeat_having_no_block(self):
        """ If repeat is called without a repeated block
        definition existing, than repeat should throw an
        exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.REPEAT_RBLOCK_2)

    def test_repeat_having_no_block_of_same_name(self):
        """ If repeat is called without a repeated block of
        the corresponding name existing, than repeat should
        throw an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block {0} tag was found before the .+ tag$".format(
                self.RBLOCK_2_NAME),
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_2)

    def test_repeated_block_with_no_args(self):
        """ repeated_block should throw an exception when
        called without arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_FEW_REPEATED_BLOCK)
    
    def test_repeated_block_with_too_many_args(self):
        """ repeated_block should throw an exception when
        called with too many arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_MANY_REPEATED_BLOCK)

    def test_repeat_with_no_args(self):
        """ repeat should throw an exception when
        called without arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_FEW_REPEAT)
    
    def test_repeat_with_too_many_args(self):
        """ repeat should throw an exception when
        called with too many arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_MANY_REPEAT)


# Tests for macros.py
from .templatetags.macros import _setup_macros_dict

class MacrosTests(TestCase):

    LOAD_MACROS = "{% load macros %}"
    TEST_LOADMACROS_TAG = (
        "{% loadmacros 'macros/test/testmacros.html' %}"
        "{% use_macro 'foo' 'bar' %}")
    
    # test assumptions
        ## no obvious assumptions made about implementation.
    
    # test functionality

    ## test _setup_macros_dict
    def test_set__setup_macros_dict_sets_variable(self):
        """ _setup_macros_dict must set the _macros
        variable on the parser.
        """
        p = make_parser("A short template")
        # check that the parser doesn't initially have the
        # _macros attribute
        self.assertFalse(hasattr(p, "_macros"))
        # check that _setup_macros_dict actually sets the
        # attribute.
        _setup_macros_dict(p)
        self.assertTrue(hasattr(p, "_macros"))

    def test_set__setup_macros_dict_doesnt_overwrite(self):
        """ _setup_macros_dict must not overwrite the
        _macros variable on the parser, if it already
        exists.
        """
        p = make_parser("A short template")
        # set the attribute to a specific dict
        dic = {'foo': 'bar', }
        p._macros = dic
        # call _setup_macros_dict and test that
        # the dict hasn't been overwritten.
        _setup_macros_dict(p)
        self.assertEqual(p._macros, dic)

    def test_set__setup_macros_dict_initialize_empty(self):
        """ Set repeated blocks must initialize the
        the _repeated_blocks variable as an empty dict.
        """
        p = make_parser("A short template")
        _setup_macros_dict(p)
        self.assertEqual(p._macros, {})

    ## test load macros

    #### contents of testmacros.html:
    """
    {% load macros %}

    {% macro test_macro arg1 arg2 kwarg1="default" %}
            arg1: {{ arg1 }};
            arg2: {{ arg2 }};
            kwarg1: {{ kwarg1 }};
    {% endmacro %}
    """

    def test_load_macros_works(self):
        """ Load macros should make the test macro
        available to the template.
        """
        p = make_parser(self.LOAD_MACROS + self.TEST_LOADMACROS_TAG)
        # parse the template to run the template tags
        nodelist = p.parse()
        # check that the macro is added to the parser
        self.assertTrue(hasattr(p, "_macros"))
        self.assertIn("test_macro", p._macros)
        # render nodelist
        c = Context({})
        rendered_template = nodelist.render(c)
        # check that the macro renders in the new template
        self.assertEqual(rendered_template,
            "\n\n\n\targ1: foo;\n\targ2: bar;\n\tkwarg1: default;\n")
    
    ## test macro, use_macro, and macro_block
    def test_macro_sets_in_parser(self):
        """ check that the macro tag actually sets
        the node in the parser.
        """
        pass

    def test_use_macro_works(self):
        """ test several use cases/renderings of the
        use_macro tag.
        """
        pass

    def test_macro_block_works(self):
        """ test several use cases/renderings of the
        macro_block tag.
        """
        pass

    def test_multiple_macros(self):
        """ test that several macros may be defined
        and used multiple times in the same template.
        """
        pass

    def test_use_macro_with_macro_block(self):
        """ test that use_macro and macro_block may
        be used in the same template, and that they
        render equivalently.
        """
        pass


    # test exceptions
