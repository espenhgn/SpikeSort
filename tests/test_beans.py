from spike_beans import base
from nose.tools import ok_, raises
from nose import with_setup


def setup():
    "set up test fixtures"
    pass


def teardown():
    "tear down test fixtures"
    base.features = base.FeatureBroker()


class Dummy(base.Component):
    con = base.RequiredFeature('Data', base.HasAttributes('data'))
    opt_con = base.OptionalFeature('OptionalData', base.HasAttributes('data'))

    def __init__(self):
        self.data = 0
        super(Dummy, self).__init__()

    def get_data(self):
        return self.con.data

    def get_optional_data(self):
        if self.opt_con:
            return self.opt_con.data

    def _update(self):
        self.data += 1

class DummyDataWithZeroDivision(object):
    @property
    def data(self):
        data = 1/0
        return data

class DummyTwoWay(Dummy):
    con2 = base.RequiredFeature('Data2', base.HasAttributes('get_data'))

    def get_data(self):
        return self.con.data + self.con2.get_data()


class DummyDataProvider(base.Component):
    data = "some data"


class NixProvider(base.Component):
    pass


@with_setup(setup, teardown)
def test_dependency_resolution():
    base.features.Provide('Data', DummyDataProvider)
    comp = Dummy()
    ok_(comp.get_data() == 'some data')


@with_setup(setup, teardown)
def test_diamond_dependency():
    base.features.Provide("Data", DummyDataProvider())
    base.features.Provide("Data2", Dummy())
    out = DummyTwoWay()
    data = out.get_data()
    base.features['Data'].update()
    print(out.data)
    ok_(out.data == 1)


@raises(AssertionError)
@with_setup(setup, teardown)
def test_missing_attribute():
    base.features.Provide('Data', NixProvider)
    comp = Dummy()
    data = comp.get_data()


@raises(AttributeError)
@with_setup(setup, teardown)
def test_missing_dependency():
    comp = Dummy()
    data = comp.get_data()


@with_setup(setup, teardown)
def test_on_change():
    base.features.Provide('Data', DummyDataProvider())
    comp = Dummy()
    comp.get_data()
    base.features['Data'].update()
    ok_(comp.data)

@raises(ZeroDivisionError)
@with_setup(setup, teardown)
def test_hasattribute_exceptions():
    '''test whether HasAttributes lets exceptions through (other than AttributeError)'''
    c = DummyDataWithZeroDivision()
    base.features.Provide('Data', c)
    comp = Dummy()
    data = comp.get_data()
    assert True

@with_setup(setup, teardown)
def test_register_new_feature_by_setitem():
    base.features['Data']=DummyDataProvider()
    comp = Dummy()
    ok_(comp.get_data() == 'some data')

@with_setup(setup, teardown)
def test_register_new_feature_by_register():
    dep_comp = DummyDataProvider()
    added_comp = base.register("Data", dep_comp)
    comp = Dummy()
    ok_(comp.get_data() == 'some data')
    assert dep_comp is added_comp

@with_setup(setup, teardown)
def test_missing_optional_dependency():
    required_dep = base.register("Data", DummyDataProvider())
    comp = Dummy()
    ok_(comp.opt_con is None)

@raises(ZeroDivisionError)
@with_setup(setup, teardown)
def test_hasattribute_exceptions_for_optional_deps():
    '''test whether HasAttributes raises exceptions for optional features'''
    required_dep = base.register("Data", DummyDataProvider())
    optional_dep = base.register('OptionalData', DummyDataWithZeroDivision())
    comp = Dummy()
    data = comp.get_optional_data()
    assert True

