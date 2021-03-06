import pytest
from functools import partial
import datetime
from lollipop.types import MISSING, ValidationError, Type, Any, String, \
    Number, Integer, Float, Boolean, DateTime, Date, Time, List, Dict, \
    Field, AttributeField, MethodField, FunctionField, ConstantField, Object, \
    Optional, LoadOnly, DumpOnly
from lollipop.errors import merge_errors
from lollipop.validators import Validator, Predicate
from collections import namedtuple


def validator(predicate, message='Something went wrong'):
    return Predicate(predicate, message)


def constant_succeed_validator():
    """Returns validator that always succeeds"""
    return validator(lambda _: True)


def constant_fail_validator(message):
    """Returns validator that always fails with given message"""
    return validator(lambda _: False, message)


def is_odd_validator():
    """Returns validator that checks if integer is odd"""
    return validator(lambda x: x % 2 == 1, 'Value should be odd')


class SpyValidator(Validator):
    def __init__(self):
        super(SpyValidator, self).__init__()
        self.validated = None
        self.context = None

    def __call__(self, value, context=None):
        self.validated = value
        self.context = context


class SpyType(Type):
    def __init__(self, load_result=None, dump_result=None):
        super(Type, self).__init__()
        self.loaded = None
        self.load_called = False
        self.load_context = None
        self.load_result = load_result
        self.dumped = None
        self.dump_called = False
        self.dump_context = None
        self.dump_result = dump_result

    def load(self, data, context=None, *args, **kwargs):
        self.loaded = data
        self.load_called = True
        self.load_context = context
        return self.load_result or data

    def dump(self, value, context=None, *args, **kwargs):
        self.dumped = value
        self.dump_called = True
        self.dump_context = context
        return self.dump_result or value


class RequiredTestsMixin:
    """Mixin that adds tests for reacting to missing/None values during load/dump.
    Host class should define `tested_type` properties.
    """
    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().load(MISSING)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().load(None)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().dump(MISSING)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().dump(None)
        assert exc_info.value.messages == Type.default_error_messages['required']


class ValidationTestsMixin:
    """Mixin that adds tests for reacting to validators.
    Host class should define `tested_type` and `valid_value` properties.
    """
    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert self.tested_type(
            validate=[constant_succeed_validator(),
                      constant_succeed_validator()],
        ).load(self.valid_data) == self.valid_value

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message1 = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type(validate=constant_fail_validator(message1))\
                .load(self.valid_data)
        assert exc_info.value.messages == message1

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type(validate=[constant_fail_validator(message1),
                                       constant_fail_validator(message2)])\
                .load(self.valid_data)
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_loading_passes_context_to_validator(self):
        context = object()
        validator = SpyValidator()
        self.tested_type(validate=validator).load(self.valid_data, context)
        assert validator.context == context


class TestString(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = String
    valid_data = 'foo'
    valid_value = 'foo'

    def test_loading_string_value(self):
        assert String().load('foo') == 'foo'

    def test_loading_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().load(123)
        assert exc_info.value.messages == String.default_error_messages['invalid']

    def test_dumping_string_value(self):
        assert String().dump('foo') == 'foo'

    def test_dumping_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().dump(123)
        assert exc_info.value.messages == String.default_error_messages['invalid']


class TestNumber(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Number
    valid_data = 1.23
    valid_value = 1.23

    def test_loading_float_value(self):
        assert Number().load(1.23) == 1.23

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Number().load("abc")
        assert exc_info.value.messages == Number.default_error_messages['invalid']

    def test_dumping_float_value(self):
        assert Number().dump(1.23) == 1.23

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Number().dump("abc")
        assert exc_info.value.messages == Number.default_error_messages['invalid']


class TestInteger:
    def test_loading_integer_value(self):
        assert Integer().load(123) == 123

    def test_loading_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().load(value) == value

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load("abc")
        assert exc_info.value.messages == Integer.default_error_messages['invalid']

    def test_dumping_integer_value(self):
        assert Integer().dump(123) == 123

    def test_dumping_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().dump(value) == value

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().dump("abc")
        assert exc_info.value.messages == Integer.default_error_messages['invalid']


class TestFloat:
    def test_loading_float_value(self):
        assert Float().load(1.23) == 1.23

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Float().load("abc")
        assert exc_info.value.messages == Float.default_error_messages['invalid']

    def test_dumping_float_value(self):
        assert Float().dump(1.23) == 1.23

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Float().dump("abc")
        assert exc_info.value.messages == Float.default_error_messages['invalid']


class TestBoolean(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Boolean
    valid_data = True
    valid_value = True

    def test_loading_boolean_value(self):
        assert Boolean().load(True) == True
        assert Boolean().load(False) == False

    def test_loading_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load("123")
        assert exc_info.value.messages == Boolean.default_error_messages['invalid']

    def test_dumping_boolean_value(self):
        assert Boolean().dump(True) == True
        assert Boolean().dump(False) == False

    def test_dumping_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().dump("123")
        assert exc_info.value.messages == Boolean.default_error_messages['invalid']


class TestDateTime(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = DateTime
    valid_data = '2016-07-28T11:22:33UTC'
    valid_value = datetime.datetime(2016, 7, 28, 11, 22, 33)

    def test_loading_string_date(self):
        assert DateTime().load('2011-12-13T11:22:33UTC') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_using_predefined_format(self):
        assert DateTime(format='rfc822').load('13 Dec 11 11:22:33 UTC') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_using_custom_format(self):
        assert DateTime(format='%m/%d/%Y %H:%M:%S').load('12/13/2011 11:22:33') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().load(123)
        assert exc_info.value.messages == \
            DateTime.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().load('12/13/2011 11:22:33')
        assert exc_info.value.messages == \
            DateTime.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(format='%Y-%m-%d %H:%M', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('12/13/2011')
        assert exc_info.value.messages == \
            'Data 12/13/2011 does not match format %Y-%m-%d %H:%M'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        DateTime(validate=validator).load('2011-12-13T11:22:33GMT')
        assert validator.validated == datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_dumping_date(self):
        assert DateTime().dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '2011-12-13T11:22:33'

    def test_dumping_using_predefined_format(self):
        assert DateTime(format='rfc822')\
            .dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '13 Dec 11 11:22:33 '

    def test_dumping_using_custom_format(self):
        assert DateTime(format='%m/%d/%Y %H:%M:%S')\
            .dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '12/13/2011 11:22:33'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().dump(123)
        assert exc_info.value.messages == DateTime.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestDate(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Date
    valid_data = '2016-07-28'
    valid_value = datetime.date(2016, 7, 28)

    def test_loading_string_date(self):
        assert Date().load('2011-12-13') == datetime.date(2011, 12, 13)

    def test_loading_using_predefined_format(self):
        assert Date(format='rfc822').load('13 Dec 11') == datetime.date(2011, 12, 13)

    def test_loading_using_custom_format(self):
        assert Date(format='%m/%d/%Y').load('12/13/2011') == \
            datetime.date(2011, 12, 13)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().load(123)
        assert exc_info.value.messages == Date.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().load('12/13/2011')
        assert exc_info.value.messages == Date.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(format='%Y-%m-%d', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('12/13/2011')
        assert exc_info.value.messages == \
            'Data 12/13/2011 does not match format %Y-%m-%d'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        Date(validate=validator).load('2011-12-13')
        assert validator.validated == datetime.date(2011, 12, 13)

    def test_dumping_date(self):
        assert Date().dump(datetime.date(2011, 12, 13)) == '2011-12-13'

    def test_dumping_using_predefined_format(self):
        assert Date(format='rfc822').dump(datetime.date(2011, 12, 13)) == '13 Dec 11'

    def test_dumping_using_custom_format(self):
        assert Date(format='%m/%d/%Y').dump(datetime.date(2011, 12, 13)) == \
            '12/13/2011'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().dump(123)
        assert exc_info.value.messages == Date.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestTime(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Time
    valid_data = '11:22:33'
    valid_value = datetime.time(11, 22, 33)

    def test_loading_string_date(self):
        assert Time().load('11:22:33') == datetime.time(11, 22, 33)

    def test_loading_using_custom_format(self):
        assert Time(format='%H %M %S').load('11 22 33') == \
            datetime.time(11, 22, 33)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().load(123)
        assert exc_info.value.messages == Time.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().load('12/13/2011')
        assert exc_info.value.messages == Time.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(format='%H:%M:%S', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('11 22 33')
        assert exc_info.value.messages == \
            'Data 11 22 33 does not match format %H:%M:%S'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        Time(validate=validator).load('11:22:33')
        assert validator.validated == datetime.time(11, 22, 33)

    def test_dumping_date(self):
        assert Time().dump(datetime.time(11, 22, 33)) == '11:22:33'

    def test_dumping_using_custom_format(self):
        assert Time(format='%H %M %S').dump(datetime.time(11, 22, 33)) == \
            '11 22 33'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().dump(123)
        assert exc_info.value.messages == Time.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestList(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(List, String())
    valid_data = ['foo', 'bar']
    valid_value = ['foo', 'bar']

    def test_loading_list_value(self):
        assert List(String()).load(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_loading_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load('1, 2, 3')
        assert exc_info.value.messages == List.default_error_messages['invalid']

    def test_loading_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load([1, '2', 3])
        message = String.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 2: message}

    def test_loading_list_value_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator())).load([1, 2, 3])
        assert exc_info.value.messages == {1: 'Value should be odd'}

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        List(inner_type).load(['foo'], context)
        assert inner_type.load_context == context

    def test_dumping_list_value(self):
        assert List(String()).dump(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_dumping_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump('1, 2, 3')
        assert exc_info.value.messages == List.default_error_messages['invalid']

    def test_dumping_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump([1, '2', 3])
        message = String.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 2: message}

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        List(inner_type).dump(['foo'], context)
        assert inner_type.dump_context == context


class TestDict(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(Dict, Integer())
    valid_data = {'foo': 123, 'bar': 456}
    valid_value = {'foo': 123, 'bar': 456}

    def test_loading_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).load({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_loading_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_loading_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load(['1', '2'])
        assert exc_info.value.messages == Dict.default_error_messages['invalid']

    def test_loading_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load({'foo': 1, 'bar': 'abc'})
        message = Integer.default_error_messages['invalid']
        assert exc_info.value.messages == {'bar': message}

    def test_loading_dict_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator())).load({'foo': 1, 'bar': 2})
        assert exc_info.value.messages == {'bar': 'Value should be odd'}

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        Dict(inner_type).load({'foo': 123}, context)
        assert inner_type.load_context == context

    def test_dumping_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).dump({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_dumping_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_dumping_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(()).dump('1, 2, 3')
        assert exc_info.value.messages == Dict.default_error_messages['invalid']

    def test_dumping_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).dump({'foo': 1, 'bar': 'abc'})
        message = Integer.default_error_messages['invalid']
        assert exc_info.value.messages == {'bar': message}

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        Dict(inner_type).dump({'foo': 123}, context)
        assert inner_type.dump_context == context

class AttributeDummy:
    foo = 'hello'
    bar = 123


class TestAttributeField:
    def test_loading_value_with_field_type(self):
        field_type = SpyType()
        assert AttributeField(field_type)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'hello'
        assert field_type.loaded == 'hello'

    def test_loading_given_attribute_regardless_of_attribute_override(self):
        assert AttributeField(String(), attribute='baz')\
            .load('foo', {'foo': 'hello', 'bar': 123, 'baz': 'goodbye'}) == 'hello'

    def test_loading_missing_value_if_attribute_does_not_exist(self):
        assert AttributeField(SpyType())\
            .load('foo', {'bar': 123, 'baz': 'goodbye'}) == MISSING

    def test_loading_passes_context_to_field_type_load(self):
        field_type = SpyType()
        context = object()
        AttributeField(field_type).load('foo', {'foo': 123}, context)
        assert field_type.load_context == context

    def test_dumping_given_attribute_from_object(self):
        assert AttributeField(SpyType())\
            .dump('foo', AttributeDummy()) == AttributeDummy().foo

    def test_dumping_object_attribute_with_field_type(self):
        field_type = SpyType()
        assert AttributeField(field_type).dump('foo', AttributeDummy())
        assert field_type.dumped == AttributeDummy().foo

    def test_dumping_a_different_attribute_from_object(self):
        assert AttributeField(SpyType(), attribute='bar')\
            .dump('foo', AttributeDummy()) == AttributeDummy().bar

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        AttributeField(field_type).dump('foo', AttributeDummy(), context)
        assert field_type.dump_context == context


class MethodDummy:
    def foo(self):
        return 'hello'

    def bar(self):
        return 123

    baz = 'goodbye'


class TestMethodField:
    def test_loading_always_returns_missing(self):
        assert MethodField(SpyType(), 'foo')\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_result_of_given_objects_method(self):
        assert MethodField(SpyType(), 'foo')\
            .dump('foo', MethodDummy()) == MethodDummy().foo()

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        assert MethodField(field_type, 'foo').dump('foo', MethodDummy())
        assert field_type.dumped == MethodDummy().foo()

    def test_dumping_result_of_a_different_obejcts_method(self):
        assert MethodField(SpyType(), method='bar')\
            .dump('foo', MethodDummy()) == MethodDummy().bar()

    def test_dumping_raises_ValueError_if_given_method_does_not_exist(self):
        with pytest.raises(ValueError):
            MethodField(SpyType(), method='unknown').dump('bam', MethodDummy())

    def test_dumping_raises_ValueError_if_given_method_is_not_callable(self):
        with pytest.raises(ValueError):
            MethodField(SpyType(), method='baz').dump('foo', MethodDummy())

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        MethodField(field_type, 'foo').dump('foo', MethodDummy(), context)
        assert field_type.dump_context == context


class TestFunctionField:
    def test_loading_always_returns_missing(self):
        assert FunctionField(SpyType(), lambda name, obj: getattr(obj, name))\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_result_of_function_call(self):
        assert FunctionField(SpyType(), lambda name, obj: getattr(obj, name))\
            .dump('foo', AttributeDummy()) == AttributeDummy().foo

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        FunctionField(field_type, lambda name, obj: getattr(obj, name))\
            .dump('foo', AttributeDummy())
        assert field_type.dumped == AttributeDummy().foo

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        FunctionField(field_type, lambda name, obj: getattr(obj, name))\
            .dump('foo', AttributeDummy(), context)
        assert field_type.dump_context == context


class TestConstantField:
    def test_loading_always_returns_missing(self):
        assert ConstantField(SpyType(), 42)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_always_returns_given_value(self):
        assert ConstantField(SpyType(), 42)\
            .dump('foo', AttributeDummy()) == 42

    def test_dumping_given_constant_with_field_type(self):
        field_type = SpyType()
        ConstantField(field_type, 42).dump('foo', AttributeDummy())
        assert field_type.dumped == 42


class AlwaysMissingType(Type):
    def load(self, data, context=None):
        return MISSING

    def dump(self, value, context=None):
        return MISSING


class AlwaysInvalidType(Type):
    def __init__(self, error_message='Invalid'):
        super(AlwaysInvalidType, self).__init__()
        self.error_message = error_message

    def load(self, data, context=None):
        raise ValidationError(self.error_message)

    def dump(self, value, context=None):
        raise ValidationError(self.error_message)


class SpyField(Field):
    def load(self, name, data, context=None):
        self.loaded = (name, data)
        return data

    def dump(self, name, obj, context=None):
        self.dumped = (name, obj)
        return obj


class TestObject(RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(Object, {'foo': String(), 'bar': Integer()})
    valid_data = {'foo': 'hello', 'bar': 123}
    valid_value = {'foo': 'hello', 'bar': 123}

    def test_loading_dict_value(self):
        assert Object({'foo': String(), 'bar': Integer()})\
            .load({'foo': 'hello', 'bar': 123}) == {'foo': 'hello', 'bar': 123}

    def test_loading_non_dict_values_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).load(['hello', 123])
        assert exc_info.value.messages == Object.default_error_messages['invalid']

    def test_loading_bypasses_values_for_which_field_type_returns_missing_value(self):
        assert Object({'foo': AlwaysMissingType(), 'bar': Integer()})\
            .load({'foo': 'hello', 'bar': 123}) == {'bar': 123}

    def test_loading_dict_with_field_errors_raises_ValidationError_with_all_field_errors_merged(self):
        message1 = 'Error 1'
        message2 = 'Error 2'
        with pytest.raises(ValidationError) as exc_info:
            Object({
                'foo': AlwaysInvalidType(message1),
                'bar': AlwaysInvalidType(message2),
                'baz': String(),
            }).load({'foo': 'hello', 'bar': 123, 'baz': 'goodbye'})

        assert exc_info.value.messages == {'foo': message1, 'bar': message2}

    def test_loading_dict_with_field_errors_does_not_run_whole_object_validators(self):
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError):
            Object({
                'foo': AlwaysInvalidType(),
                'bar': AlwaysInvalidType(),
                'baz': String(),
            }, validate=validate).load({'foo': 'hello', 'bar': 123, 'baz': 'goodbye'})

        assert validate.called == 0

    def test_loading_calls_field_load_passing_field_name_and_whole_data(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        data = {'foo': 'hello', 'bar': 123}
        Object({'foo': foo_field, 'bar': bar_field}).load(data)
        assert foo_field.loaded == ('foo', data)
        assert bar_field.loaded == ('bar', data)

    def test_loading_passes_context_to_inner_type_load(self):
        foo_type = SpyType()
        bar_type = SpyType()
        context = object()
        Object({'foo': foo_type, 'bar': bar_type})\
            .load({'foo': 'hello', 'bar': 123}, context)
        assert foo_type.load_context == context
        assert bar_type.load_context == context

    def test_constructing_custom_objects_on_load(self):
        MyData = namedtuple('MyData', ['foo', 'bar'])
        assert Object({'foo': String(), 'bar': Integer()}, constructor=MyData)\
            .load({'foo': 'hello', 'bar': 123}) == MyData('hello', 123)

    def test_load_ignores_extra_fields_by_default(self):
        assert Object({'foo': String()})\
            .load({'foo': 'hello', 'bar': 123}) == {'foo': 'hello'}

    def test_load_raises_ValidationError_if_reporting_extra_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String()}, allow_extra_fields=False)\
                .load({'foo': 'hello', 'bar': 123, 'baz': True})

        unknown = Object.default_error_messages['unknown']
        assert exc_info.value.messages == {'bar': unknown, 'baz': unknown}

    def test_dumping_object_attributes(self):
        MyData = namedtuple('MyData', ['foo', 'bar'])
        assert Object({'foo': String(), 'bar': Integer()})\
            .dump(MyData('hello', 123)) == {'foo': 'hello', 'bar': 123}

    def test_dumping_calls_field_dump_passing_field_name_and_whole_object(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        MyData = namedtuple('MyData', ['foo', 'bar'])
        obj = MyData('hello', 123)
        Object({'foo': foo_field, 'bar': bar_field}).dump(obj)
        assert foo_field.dumped == ('foo', obj)
        assert bar_field.dumped == ('bar', obj)

    def test_dumping_passes_context_to_inner_type_dump(self):
        foo_type = SpyType()
        bar_type = SpyType()
        context = object()
        Object({'foo': foo_type, 'bar': bar_type})\
            .dump(AttributeDummy(), context)
        assert foo_type.dump_context == context
        assert bar_type.dump_context == context


class TestOptional:
    def test_loading_value_calls_load_of_inner_type(self):
        inner_type = SpyType()
        Optional(inner_type).load('foo')
        assert inner_type.loaded == 'foo'

    def test_loading_missing_value_returns_None(self):
        assert Optional(Any()).load(MISSING) == None

    def test_loading_None_returns_None(self):
        assert Optional(Any()).load(None) == None

    def test_loading_missing_value_does_not_call_inner_type_load(self):
        inner_type = SpyType()
        Optional(inner_type).load(None)
        assert not inner_type.load_called

    def test_loading_None_does_not_call_inner_type_load(self):
        inner_type = SpyType()
        Optional(inner_type).load(MISSING)
        assert not inner_type.load_called

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        Optional(inner_type).load('foo', context)
        assert inner_type.load_context == context

    def test_overriding_missing_value_on_load(self):
        assert Optional(Any(), load_default='foo').load(MISSING) == 'foo'

    def test_overriding_None_value_on_load(self):
        assert Optional(Any(), load_default='foo').load(None) == 'foo'

    def test_dumping_value_calls_dump_of_inner_type(self):
        inner_type = SpyType()
        Optional(inner_type).dump('foo')
        assert inner_type.dumped == 'foo'

    def test_dumping_missing_value_returns_None(self):
        assert Optional(Any()).dump(MISSING) == None

    def test_dumping_None_returns_None(self):
        assert Optional(Any()).dump(None) == None

    def test_dumping_missing_value_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        Optional(inner_type).dump(MISSING)
        assert not inner_type.dump_called

    def test_dumping_None_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        Optional(inner_type).dump(None)
        assert not inner_type.dump_called

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        Optional(inner_type).dump('foo', context)
        assert inner_type.dump_context == context

    def test_overriding_missing_value_on_dump(self):
        assert Optional(Any(), dump_default='foo').dump(MISSING) == 'foo'

    def test_overriding_None_value_on_dump(self):
        assert Optional(Any(), dump_default='foo').dump(None) == 'foo'


class TestLoadOnly:
    def test_loading_returns_inner_type_load_result(self):
        inner_type = SpyType(load_result='bar')
        assert LoadOnly(inner_type).load('foo') == 'bar'
        assert inner_type.load_called

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        LoadOnly(inner_type).load('foo', context)
        assert inner_type.load_context == context

    def test_dumping_always_returns_missing(self):
        assert LoadOnly(Any()).dump('foo') == MISSING

    def test_dumping_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        LoadOnly(inner_type).dump('foo')
        assert not inner_type.dump_called


class TestDumpOnly:
    def test_loading_always_returns_missing(self):
        assert DumpOnly(Any()).load('foo') == MISSING

    def test_loading_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        DumpOnly(inner_type).load('foo')
        assert not inner_type.load_called

    def test_dumping_returns_inner_type_dump_result(self):
        inner_type = SpyType(dump_result='bar')
        assert DumpOnly(inner_type).dump('foo') == 'bar'
        assert inner_type.dump_called

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        DumpOnly(inner_type).dump('foo', context)
        assert inner_type.dump_context == context
