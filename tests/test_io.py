import os
import filecmp
import json
import glob
import tempfile

from nose.tools import ok_, eq_, raises
import tables
import numpy as np

from spike_sort.io.filters import BakerlabFilter, PyTablesFilter
from spike_sort.io import export
from spike_sort.io import neo_filters

class TestNeo:

    def setUp(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self.samples_dir = os.path.join(path, 'samples')
        self.file_names = {'Axon': 'axonio.abf'}

    def test_read_abf(self):
        fname = self.file_names['Axon']
        file_path = os.path.join(self.samples_dir, fname)
        abf = neo_filters.AxonFilter(file_path)
        sp = abf.read_sp()
        assert len(np.array(sp['data']))>0
        assert sp['FS'] == 125000
    
    def test_read_abf_via_component(self):
        fname = self.file_names['Axon']
        file_path = os.path.join(self.samples_dir, fname)
        source = neo_filters.NeoSource(file_path)
        sp = source.read_sp()
        assert len(np.array(sp['data']))>0

class TestHDF(object):
    def setUp(self):
        self.data = np.random.randint(1000, size=(4, 100))
        self.spt = np.random.randint(0, 100, (10,)) / 200.0
        self.el_node = '/Subject/Session/Electrode'
        self.fname = 'test.h5'
        self.cell_node = self.el_node + '/cell'
        self.h5f = tables.openFile(self.fname, 'a')

        self.spt.sort()
        atom = tables.Atom.from_dtype(self.data.dtype)
        shape = self.data.shape
        filter = tables.Filters(complevel=0, complib='zlib')
        new_array = self.h5f.createCArray(self.el_node, "raw", atom, shape,
                                     filters=filter,
                                     createparents=True)
        self.sampfreq = 5.0E3
        new_array.attrs['sampfreq'] = self.sampfreq
        new_array[:] = self.data
        self.h5f.createArray(self.el_node, "cell", self.spt,
                                         title="",
                                         createparents="True")
        self.h5f.close()

    def tearDown(self):
        self.filter.close()
        os.unlink(self.fname)

    def test_write(self):
        sp_dict = {'data': self.data, 'FS': self.sampfreq}
        spt_dict = {'data': self.spt}
        self.filter = PyTablesFilter("test2.h5")
        self.filter.write_sp(sp_dict, self.el_node + "/raw")
        self.filter.write_spt(spt_dict, self.cell_node)
        self.filter.close()
        exit_code = os.system('h5diff ' + self.fname + ' test2.h5')
        os.unlink("test2.h5")
        ok_(exit_code == 0)

    def test_read_sp(self):
        self.filter = PyTablesFilter(self.fname)
        sp = self.filter.read_sp(self.el_node)
        ok_((sp['data'][:] == self.data).all())

    def test_read_sp_attr(self):
        #check n_contacts attribute
        self.filter = PyTablesFilter(self.fname)
        sp = self.filter.read_sp(self.el_node)
        n_contacts = sp['n_contacts']
        ok_(n_contacts == self.data.shape[0])

    def test_read_spt(self):
        self.filter = PyTablesFilter(self.fname)
        spt = self.filter.read_spt(self.cell_node)
        ok_((spt['data'] == self.spt).all())


class TestBakerlab(object):
    def setup(self):
        file_descr = {"fspike": "{ses_id}{el_id}.sp",
                      "cell": "{ses_id}{el_id}{cell_id}.spt",
                      "dirname": ".",
                      "FS": 5.E3,
                      "n_contacts": 1}
        self.el_node = '/Test/s32test01/el1'
        self.cell_node = self.el_node + '/cell1'
        self.data = np.random.randint(-1000, 1000, (100,))
        self.spt_data = np.random.randint(0, 100, (10,)) / 200.0
        self.spt_metadata = {'element1': 5, 'element2': 10}
        self.conf_file = 'test.conf'
        self.fname = "32test011.sp"
        self.spt_fname = "32test0111.spt"
        self.spt_log_fname = "32test0111.log"

        with open(self.conf_file, 'w') as fp:
            json.dump(file_descr, fp)

        self.data.astype(np.int16).tofile(self.fname)
        (self.spt_data * 200).astype(np.int32).tofile(self.spt_fname)

        with open(self.spt_log_fname, 'w') as lf:
            json.dump(self.spt_metadata, lf)

    def tearDown(self):
        os.unlink(self.conf_file)
        os.unlink(self.fname)
        os.unlink(self.spt_fname)
        os.unlink(self.spt_log_fname)

    def test_write_spt(self):
        cell_node_tmp = '/Test/s32test01/el2/cell1'
        spt_dict = {'data': self.spt_data}
        filter = BakerlabFilter(self.conf_file)
        filter.write_spt(spt_dict,  cell_node_tmp)
        files_eq = filecmp.cmp(self.spt_fname, "32test0121.spt", shallow=0)
        os.unlink("32test0121.spt")
        ok_(files_eq)

    def test_write_spt_metadata(self):
        cell_node_tmp = '/Test/s32test01/el2/cell1'
        spt_dict = {'data': self.spt_data,
                    'metadata': self.spt_metadata}
        filter = BakerlabFilter(self.conf_file)
        filter.write_spt(spt_dict,  cell_node_tmp, overwrite=True)
        files_eq = filecmp.cmp(self.spt_log_fname, "32test0121.log", shallow=0)
        os.unlink("32test0121.spt")
        os.unlink("32test0121.log")
        ok_(files_eq)

    @raises(IOError)
    def test_writespt_overwrite_exc(self):
        cell_node_tmp = '/Test/s32test01/el1/cell1'
        spt_dict = {'data': self.spt_data}
        filter = BakerlabFilter(self.conf_file)
        filter.write_spt(spt_dict, cell_node_tmp)

    def test_read_spt(self):
        filter = BakerlabFilter(self.conf_file)
        sp = filter.read_spt(self.cell_node)
        read_data = sp['data']
        ok_((np.abs(read_data - self.spt_data) <= 1 / 200.0).all())

    def test_write_sp(self):
        el_node_tmp = '/Test/s32test01/el2'
        sp_dict = {'data': self.data[np.newaxis, :]}
        filter = BakerlabFilter(self.conf_file)
        filter.write_sp(sp_dict, el_node_tmp)
        files_eq = filecmp.cmp("32test011.sp", "32test012.sp", shallow=0)
        os.unlink("32test012.sp")
        ok_(files_eq)

    def test_write_multichan(self):
        n_contacts = 4
        data = np.repeat(self.data[np.newaxis, :], n_contacts, 0)
        sp_dict = {'data': data}
        with open(self.conf_file, 'r+') as fid:
            file_desc = json.load(fid)
            file_desc['n_contacts'] = 4
            file_desc["fspike"] = "test{contact_id}.sp"
            fid.seek(0)
            json.dump(file_desc, fid)
        filter = BakerlabFilter(self.conf_file)
        filter.write_sp(sp_dict, self.el_node)
        all_chan_files = glob.glob("test?.sp")
        [os.unlink(p) for p in all_chan_files]
        eq_(len(all_chan_files), n_contacts)

    def test_read_sp(self):
        filter = BakerlabFilter(self.conf_file)
        sp = filter.read_sp(self.el_node)
        read_data = sp['data'][0, :]
        print(read_data.shape)
        ok_((np.abs(read_data - self.data) <= 1 / 200.0).all())

    def test_sp_shape(self):
        with open(self.conf_file, 'r+') as fid:
            file_desc = json.load(fid)
            file_desc['n_contacts'] = 4
            fid.seek(0)
            json.dump(file_desc, fid)
        filter = BakerlabFilter(self.conf_file)
        sp = filter.read_sp(self.el_node)
        data = sp['data']
        ok_(data.shape == (4, len(self.data)))


class TestExport(object):
    def test_export_cells(self):
        n_cells = 4
        self.spt_data = np.random.randint(0, 10000, (100, n_cells))
        self.spt_data.sort(0)
        self.cells_dict = dict([(i, {"data": self.spt_data[:, i]})
                           for i in range(n_cells)])
        tempdir = tempfile.mkdtemp()
        fname = os.path.join(tempdir, "test.h5")
        ptfilter = PyTablesFilter(fname)
        tmpl = "/Subject/Session/Electrode/Cell{cell_id}"
        export.export_cells(ptfilter, tmpl, self.cells_dict)
        test = []
        for i in range(n_cells):
            spt_dict = ptfilter.read_spt(tmpl.format(cell_id=i))
            test.append((spt_dict['data'] == self.spt_data[:, i]).all())
        test = np.array(test)
        ptfilter.close()
        
        os.unlink(fname)
        os.rmdir(tempdir)

        ok_(test.all())
