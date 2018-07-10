# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict
from wolframclient.utils.datastructures import Association
from wolframclient.exception import WolframParserException
from wolframclient.language.expression import WLSymbol, WLFunction
from wolframclient.utils.api import numpy
from wolframclient.serializers.wxfencoder import wxfexpr
from wolframclient.exception import WolframParserException
from functools import update_wrapper

__all__ = ['WXFConsumer', 'WXFConsumerNumpy']

class WXFConsumer(object):

    _mapping = {
        wxfexpr.WXF_CONSTANTS.Function: 'consume_function',
        wxfexpr.WXF_CONSTANTS.Symbol: 'consume_symbol',
        wxfexpr.WXF_CONSTANTS.String: 'consume_string',
        wxfexpr.WXF_CONSTANTS.BinaryString: 'consume_binary_string',
        wxfexpr.WXF_CONSTANTS.Integer8: 'consume_integer8',
        wxfexpr.WXF_CONSTANTS.Integer16: 'consume_integer16',
        wxfexpr.WXF_CONSTANTS.Integer32: 'consume_integer32',
        wxfexpr.WXF_CONSTANTS.Integer64: 'consume_integer64',
        wxfexpr.WXF_CONSTANTS.Real64: 'consume_real64',
        wxfexpr.WXF_CONSTANTS.BigInteger: 'consume_bigint',
        wxfexpr.WXF_CONSTANTS.BigReal: 'consume_bigreal',
        wxfexpr.WXF_CONSTANTS.PackedArray: 'consume_packed_array',
        wxfexpr.WXF_CONSTANTS.RawArray: 'consume_raw_array',
        wxfexpr.WXF_CONSTANTS.Association: 'consume_association',
        wxfexpr.WXF_CONSTANTS.Rule: 'consume_rule',
        wxfexpr.WXF_CONSTANTS.RuleDelayed: 'consume_rule_delayed'
    }

    def __init__(self):
        pass

    def next_expression(self, tokens, **kwargs):
        """Deserialize the next expression starting at the next token yield by `tokens`."""
        token = next(tokens)
        consumer = self._consumer_from_type(token.wxf_type)
        return consumer(token, tokens, **kwargs)

    def _consumer_from_type(self, wxf_type):
        func = WXFConsumer._mapping.get(wxf_type, None)
        if func is None:
            raise WolframParserException('Class %s does not implement any consumer method for WXF token %s' %s (cls.__name__, token))
        return getattr(self, func)

    def consume_function(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *function*.
        
        Return a :class:`list` if the head is symbol `List`, otherwise return a :class:`~wolframclient.language.expression.WLFunction`
        """
        head = next(tokens)
        args = []
        for i in range(current_token.length):
            args.append(self.next_expression(tokens, **kwargs))
        if head.wxf_type == wxfexpr.WXF_CONSTANTS.Symbol and head.data == 'List':
            return args
        else:
            return WLFunction(head.data, *args)

    def consume_association(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *association*.

        By default, return a :class:`dict` made from the rules.
        The named option `ordered_dict` can be set to `True` in which case an instance of 
        :class:`~collections.OrderedDict` is returned.
        The named option `association` can be set to `True` in which case an instance of 
        :class:`~wolframclient.utils.datastrucutres.Association` is returned.
        """
        if kwargs.get('ordered_dict', False):
            o = OrderedDict()
        elif kwargs.get('association', False):
            o = Association()
        else:
            o = {}
        for i in range(current_token.length):
            rule = self.next_expression(tokens, **kwargs)
            if isinstance(rule, tuple) and len(rule) == 2:
                o[rule[0]] = rule[1]
            else:
                raise WolframParserException(
                    'Invalid rule. Rule must be parsed as a tuple of two values.')
        return o

    def consume_rule(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *rule* as a tuple"""
        return (self.next_expression(tokens, **kwargs), self.next_expression(tokens, **kwargs))

    def consume_rule_delayed(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *rule* as a tuple"""
        return (self.next_expression(tokens, **kwargs), self.next_expression(tokens, **kwargs))

    def consume_symbol(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *symbol* as a :class:`~wolframclient.language.expression.WLSymbol`"""
        return WLSymbol(current_token.data)

    def consume_bigint(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *big integer* as a :class:`int`."""
        try:
            return int(current_token.data)
        except ValueError:
            raise WolframParserException(
                'Invalid big integer value: %s' % current_token.data)

    def consume_bigreal(self, current_token, tokens, **kwargs):
        """Parse a WXF big real as a WXF serializable big real.

        There is not such thing as a big real, in Wolfram Language notation, in Python. This 
        wrapper ensures round tripping of big reals without the need of `ToExpression`.
        Introducing `ToExpression` would imply to marshall the big real data to avoid malicious
        code from being introduced in place of an actual real.
        """
        return wxfexpr.WXFExprBigReal(current_token.data)

    def consume_string(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *string* as a string of unicode utf8 encoded."""
        return current_token.data

    def consume_binary_string(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *binary string* as a string of bytes."""
        return current_token.data

    def consume_integer8(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *integer* as a :class:`int`."""
        return current_token.data

    def consume_integer16(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *integer* as a :class:`int`."""
        return current_token.data

    def consume_integer32(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *integer* as a :class:`int`."""
        return current_token.data

    def consume_integer64(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *integer* as a :class:`int`."""
        return current_token.data

    def consume_real64(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *real* as a :class:`float`."""
        return current_token.data

    def consume_raw_array(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *raw array*. 
        
        This method must be implemented by subclasses."""
        raise NotImplementedError(
            'Method consume_raw_array is not implemented by %s.' % self.__class__.__name__)

    def consume_packed_array(self, current_token, tokens, **kwargs):
        """Consume a :class:`~wolframclient.deserializers.wxf.wxfparser.WXFToken` of type *packed array*. 
        
        This method must be implemented by subclasses."""
        raise NotImplementedError(
            'Method consume_packed_array is not implemented by %s.' % self.__class__.__name__)


class WXFConsumerNumpy(WXFConsumer):
    """Deserialize WXF array types as numpy arrays."""
    def __init__(self):
        super(WXFConsumerNumpy, self).__init__()
    
    def consume_array(self, current_token, tokens, **kwargs):
        arr=numpy.fromstring(current_token.data, dtype=WXF_TYPE_TO_DTYPE[current_token.array_type])
        numpy.reshape(arr, tuple(current_token.dimensions))
        return arr
    """Build a numpy array from a PackedArray."""
    consume_packed_array = consume_array

    """Build a numpy array from a RawArray."""
    consume_raw_array = consume_array

    WXF_TYPE_TO_DTYPE = {
        wxfexpr.ARRAY_TYPES.Integer8: 'int8',
        wxfexpr.ARRAY_TYPES.Integer16: 'int16',
        wxfexpr.ARRAY_TYPES.Integer32: 'int32',
        wxfexpr.ARRAY_TYPES.Integer64: 'int64',
        wxfexpr.ARRAY_TYPES.UnsignedInteger8: 'uint8',
        wxfexpr.ARRAY_TYPES.UnsignedInteger16: 'uint16',
        wxfexpr.ARRAY_TYPES.UnsignedInteger32: 'uint32',
        wxfexpr.ARRAY_TYPES.UnsignedInteger64: 'uint64',
        wxfexpr.ARRAY_TYPES.Real32: 'float32',
        wxfexpr.ARRAY_TYPES.Real64: 'float64',
        wxfexpr.ARRAY_TYPES.ComplexReal32: 'complex64',
        wxfexpr.ARRAY_TYPES.ComplexReal64: 'complex128',
    }
