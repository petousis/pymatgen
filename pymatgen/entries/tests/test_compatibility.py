# coding: utf-8

from __future__ import division, unicode_literals

"""
Created on Mar 19, 2012
"""


__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__date__ = "Mar 19, 2012"

import os
import unittest

from pymatgen.entries.compatibility import MaterialsProjectCompatibility, \
    MITCompatibility, AqueousCorrection, MITAqueousCompatibility, MaterialsProjectAqueousCompatibility
from pymatgen.entries.computed_entries import ComputedEntry, \
    ComputedStructureEntry
from pymatgen import Composition, Lattice, Structure, Element


class MaterialsProjectCompatibilityTest(unittest.TestCase):

    def setUp(self):
        self.entry1 = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.entry2 = ComputedEntry(
            'Fe3O4', -2, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.entry3 = ComputedEntry(
            'FeO', -2, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 4.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
    def test_process_entry(self):
        compat = MaterialsProjectCompatibility()
        ggacompat = MaterialsProjectCompatibility("GGA")

        #Correct parameters
        self.assertIsNotNone(compat.process_entry(self.entry1))
        self.assertIsNone(ggacompat.process_entry(self.entry1))

        #Correct parameters
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': False, "hubbards": {}, 'run_type': 'GGA',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))
        self.assertIsNotNone(ggacompat.process_entry(entry))

        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNotNone(compat.process_entry(entry))

        #Check actual correction
        self.assertAlmostEqual(compat.process_entry(entry).correction,
                               - 2.733 * 2 - 0.70229 * 3)

        entry = ComputedEntry(
            'FeF3', -2, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'F': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE F 08Apr2002']})
        self.assertIsNotNone(compat.process_entry(entry))

        #Check actual correction
        self.assertAlmostEqual(compat.process_entry(entry).correction, -2.733)

        #Wrong U value
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 5.2, 'O': 0}, 'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #GGA run of U
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': False, 'hubbards': None,
                        'run_type': 'GGA',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #GGA+U run of non-U
        entry = ComputedEntry(
            'Al2O3', -1, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Al': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Al 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #Materials project should not have a U for sulfides
        entry = ComputedEntry(
            'FeS2', -2, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'S': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE S 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #Wrong psp
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #Testing processing of elements.
        entry = ComputedEntry(
            'O', -1, 0.0,
            parameters={'is_hubbard': False, 'hubbards': {},
                        'potcar_symbols': ['PAW_PBE O 08Apr2002'],
                        'run_type': 'GGA'})
        entry = compat.process_entry(entry)
#        self.assertEqual(entry.entry_id, -8)
        self.assertAlmostEqual(entry.energy, -1)
        self.assertAlmostEqual(ggacompat.process_entry(entry).energy,
                               -1)

    def test_get_corrections_dict(self):
        compat = MaterialsProjectCompatibility()
        ggacompat = MaterialsProjectCompatibility("GGA")

        #Correct parameters
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True, 'hubbards': {'Fe': 5.3, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        c = compat.get_corrections_dict(entry)

        self.assertAlmostEqual(c["MP Gas Correction"], -2.10687)
        self.assertAlmostEqual(c["MP Advanced Correction"], -5.466)

        entry.parameters["is_hubbard"] = False
        del entry.parameters["hubbards"]
        c = ggacompat.get_corrections_dict(entry)
        self.assertNotIn("MP Advanced Correction", c)

    def test_process_entries(self):
        compat = MaterialsProjectCompatibility()
        entries = compat.process_entries([self.entry1, self.entry2,
                                          self.entry3])
        self.assertEqual(len(entries), 2)


class MITCompatibilityTest(unittest.TestCase):

    def test_process_entry(self):
        compat = MITCompatibility()

        #Correct parameters
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 4.0, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNotNone(compat.process_entry(entry))
        self.assertAlmostEqual(compat.process_entry(entry).correction,
                               - 1.723 * 2 -0.66975*3)

        entry = ComputedEntry(
            'FeF3', -2, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 4.0, 'F': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE F 08Apr2002']})
        self.assertIsNotNone(compat.process_entry(entry))

        #Check actual correction
        self.assertAlmostEqual(compat.process_entry(entry).correction, -1.723)

        #MIT should not have a U for sulfides
        entry = ComputedEntry(
            'FeS2', -2, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 1.9, 'S': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE S 08Apr2002']})
        self.assertIsNotNone(compat.process_entry(entry))

        self.assertAlmostEqual(compat.process_entry(entry).correction, -1.113)

        #Wrong U value
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 5.2, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #GGA run
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': False,
                        'hubbards': None,
                        'run_type': 'GGA',
                        'potcar_symbols': ['PAW_PBE Fe 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #Wrong psp
        entry = ComputedEntry(
            'Fe2O3', -1, 0.0,
            parameters={'is_hubbard': True,
                        'hubbards': {'Fe': 4.0, 'O': 0},
                        'run_type': 'GGA+U',
                        'potcar_symbols': ['PAW_PBE Fe_pv 06Sep2000',
                                           'PAW_PBE O 08Apr2002']})
        self.assertIsNone(compat.process_entry(entry))

        #Testing processing of elements.
        entry = ComputedEntry(
            'O', -1, 0.0,
            parameters={'is_hubbard': False, 'hubbards': {},
                        'potcar_symbols': ['PAW_PBE O 08Apr2002'],
                        'run_type': 'GGA'})
        entry = compat.process_entry(entry)
        self.assertAlmostEqual(entry.energy, -1)


class OxideTypeCorrectionTest(unittest.TestCase):

    def setUp(self):
        self.compat = MITCompatibility()

    def test_no_struct_compat(self):
        lio2_entry_nostruct = ComputedEntry(Composition("Li2O4"), -3,
                                            data={"oxide_type": "superoxide"},
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        lio2_entry_corrected = self.compat.process_entry(lio2_entry_nostruct)
        self.assertAlmostEqual(lio2_entry_corrected.energy, -3 - 0.13893*4, 4)

    def test_process_entry_superoxide(self):
        el_li = Element("Li")
        el_o = Element("O")
        latt = Lattice([[3.985034, 0.0, 0.0],
                        [0.0, 4.881506, 0.0],
                        [0.0, 0.0, 2.959824]])
        elts = [el_li, el_li, el_o, el_o, el_o, el_o]
        coords = list()
        coords.append([0.500000, 0.500000, 0.500000])
        coords.append([0.0, 0.0, 0.0])
        coords.append([0.632568, 0.085090, 0.500000])
        coords.append([0.367432, 0.914910, 0.500000])
        coords.append([0.132568, 0.414910, 0.000000])
        coords.append([0.867432, 0.585090, 0.000000])
        struct = Structure(latt, elts, coords)
        lio2_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        lio2_entry_corrected = self.compat.process_entry(lio2_entry)
        self.assertAlmostEqual(lio2_entry_corrected.energy, -3 -0.13893*4, 4)

    def test_process_entry_peroxide(self):
        latt = Lattice.from_parameters(3.159597, 3.159572, 7.685205, 89.999884, 89.999674, 60.000510)
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_li, el_li, el_li, el_o, el_o, el_o, el_o]
        coords = [[0.666656, 0.666705, 0.750001],
                  [0.333342, 0.333378, 0.250001],
                  [0.000001, 0.000041, 0.500001],
                  [0.000001, 0.000021, 0.000001],
                  [0.333347, 0.333332, 0.649191],
                  [0.333322, 0.333353, 0.850803],
                  [0.666666, 0.666686, 0.350813],
                  [0.666665, 0.666684, 0.149189]]
        struct = Structure(latt, elts, coords)
        li2o2_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        li2o2_entry_corrected = self.compat.process_entry(li2o2_entry)
        self.assertAlmostEqual(li2o2_entry_corrected.energy, -3 - 0.44317 * 4, 4)

    def test_process_entry_ozonide(self):
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_o, el_o, el_o]
        latt = Lattice.from_parameters(3.999911, 3.999911, 3.999911,
                                       133.847504, 102.228244, 95.477342)
        coords = [[0.513004, 0.513004, 1.000000],
                  [0.017616, 0.017616, 0.000000],
                  [0.649993, 0.874790, 0.775203],
                  [0.099587, 0.874790, 0.224797]]
        struct = Structure(latt, elts, coords)
        lio3_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        lio3_entry_corrected = self.compat.process_entry(lio3_entry)
        self.assertAlmostEqual(lio3_entry_corrected.energy, -3.0)

    def test_process_entry_oxide(self):
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_li, el_o]
        latt = Lattice.from_parameters(3.278, 3.278, 3.278,
                                       60, 60, 60)
        coords = [[0.25, 0.25, 0.25],
                  [0.75, 0.75, 0.75],
                  [0.0, 0.0, 0.0]]
        struct = Structure(latt, elts, coords)
        li2o_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        li2o_entry_corrected = self.compat.process_entry(li2o_entry)
        self.assertAlmostEqual(li2o_entry_corrected.energy, -3.0 -0.66975, 4)


class OxideTypeCorrectionNoPeroxideCorrTest(unittest.TestCase):

    def setUp(self):
        self.compat = MITCompatibility(correct_peroxide=False)

    def test_oxide_energy_corr(self):
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_li, el_o]
        latt = Lattice.from_parameters(3.278, 3.278, 3.278,
                                       60, 60, 60)
        coords = [[0.25, 0.25, 0.25],
                  [0.75, 0.75, 0.75],
                  [0.0, 0.0, 0.0]]
        struct = Structure(latt, elts, coords)
        li2o_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        li2o_entry_corrected = self.compat.process_entry(li2o_entry)
        self.assertAlmostEqual(li2o_entry_corrected.energy, -3.0 -0.66975, 4)

    def test_peroxide_energy_corr(self):
        latt = Lattice.from_parameters(3.159597, 3.159572, 7.685205, 89.999884, 89.999674, 60.000510)
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_li, el_li, el_li, el_o, el_o, el_o, el_o]
        coords = [[0.666656, 0.666705, 0.750001],
                  [0.333342, 0.333378, 0.250001],
                  [0.000001, 0.000041, 0.500001],
                  [0.000001, 0.000021, 0.000001],
                  [0.333347, 0.333332, 0.649191],
                  [0.333322, 0.333353, 0.850803],
                  [0.666666, 0.666686, 0.350813],
                  [0.666665, 0.666684, 0.149189]]
        struct = Structure(latt, elts, coords)
        li2o2_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        li2o2_entry_corrected = self.compat.process_entry(li2o2_entry)
        self.assertRaises(AssertionError, self.assertAlmostEqual,
                           *(li2o2_entry_corrected.energy, -3 - 0.44317 * 4, 4))
        self.assertAlmostEqual(li2o2_entry_corrected.energy, -3 - 0.66975 * 4, 4)

    def test_ozonide(self):
        el_li = Element("Li")
        el_o = Element("O")
        elts = [el_li, el_o, el_o, el_o]
        latt = Lattice.from_parameters(3.999911, 3.999911, 3.999911,
                                       133.847504, 102.228244, 95.477342)
        coords = [[0.513004, 0.513004, 1.000000],
                  [0.017616, 0.017616, 0.000000],
                  [0.649993, 0.874790, 0.775203],
                  [0.099587, 0.874790, 0.224797]]
        struct = Structure(latt, elts, coords)
        lio3_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 06Sep2000', 'PAW_PBE O 08Apr2002']})
        lio3_entry_corrected = self.compat.process_entry(lio3_entry)
        self.assertAlmostEqual(lio3_entry_corrected.energy, -3.0 - 3 * 0.66975)


class AqueousCorrectionTest(unittest.TestCase):

    def setUp(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        fp = os.path.join(module_dir, os.path.pardir, "MITCompatibility.yaml")
        self.corr = AqueousCorrection(fp)

    def test_compound_energy(self):

        O2_entry = self.corr.correct_entry(ComputedEntry(Composition("O2"),
                                                          -4.9355 * 2))
        H2_entry = self.corr.correct_entry(ComputedEntry(Composition("H2"), 3))
        H2O_entry = self.corr.correct_entry(ComputedEntry(Composition("H2O"), 3))
        H2O_formation_energy = H2O_entry.energy - (H2_entry.energy +
                                                    O2_entry.energy / 2.0)
        self.assertAlmostEqual(H2O_formation_energy, -2.46, 2)

        entry = ComputedEntry(Composition("H2O"), -16)
        entry = self.corr.correct_entry(entry)
        self.assertAlmostEqual(entry.energy, -14.916, 4)

        entry = ComputedEntry(Composition("H2O"), -24)
        entry = self.corr.correct_entry(entry)
        self.assertAlmostEqual(entry.energy, -14.916, 4)

        entry = ComputedEntry(Composition("Cl"), -24)
        entry = self.corr.correct_entry(entry)
        self.assertAlmostEqual(entry.energy, -24.344373, 4)


class TestMITAqueousCompatibility(unittest.TestCase):

    def setUp(self):
        self.compat = MITCompatibility()
        self.aqcompat = MITAqueousCompatibility()
        module_dir = os.path.dirname(os.path.abspath(__file__))
        fp = os.path.join(module_dir, os.path.pardir, "MITCompatibility.yaml")
        self.aqcorr =  AqueousCorrection(fp)

    def test_aqueous_compat(self):

        el_li = Element("Li")
        el_o = Element("O")
        el_h = Element("H")
        latt = Lattice.from_parameters(3.565276, 3.565276, 4.384277, 90.000000, 90.000000, 90.000000)
        elts = [el_h, el_h, el_li, el_li, el_o, el_o]
        coords = [[0.000000, 0.500000, 0.413969],
                  [0.500000, 0.000000, 0.586031],
                  [0.000000, 0.000000, 0.000000],
                  [0.500000, 0.500000, 0.000000],
                  [0.000000, 0.500000, 0.192672],
                  [0.500000, 0.000000, 0.807328]]
        struct = Structure(latt, elts, coords)
        lioh_entry = ComputedStructureEntry(struct, -3,
                                            parameters={'is_hubbard': False,
                                          'hubbards': None,
                                          'run_type': 'GGA',
                                          'potcar_symbols':
        ['PAW_PBE Fe 17Jan2003', 'PAW_PBE O 08Apr2002', 'PAW_PBE H 15Jun2001']})
        lioh_entry_compat = self.compat.process_entry(lioh_entry)
        lioh_entry_compat_aqcorr = self.aqcorr.correct_entry(lioh_entry_compat)
        lioh_entry_aqcompat = self.aqcompat.process_entry(lioh_entry)
        self.assertAlmostEqual(lioh_entry_compat_aqcorr.energy, lioh_entry_aqcompat.energy, 4)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
