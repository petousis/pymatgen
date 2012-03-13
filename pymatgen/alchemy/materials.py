#!/usr/bin/env python

'''
This module performs list of transformations on list of entries, and provides a 
consistent input vs output interface for transformations on db entries.
'''

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "1.0"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Mar 2, 2012"

import os
import re
import datetime
import json

from pymatgen.core.structure import Structure
from pymatgen.io.cifio import CifParser
from pymatgen.io.vaspio import Poscar
from pymatgen.transformations.standard_transformations import transformation_from_dict
from collections import Iterable

class TransformedStructure(object):
    """
    Container object for new structures that include history of transformations.
    
    Each transformed structure is made up of a sequence of structures with associated
    transformation history.
    """

    def __init__(self, structure, transformations, history = None):
        """
        Standard constructor for a TransformedStructure
        
        Args:
            structure:
                input structure
            transformations:
                sequence of transformations to be applied to the input structure.
            history:
                optional history for the input structure, which provides a way
                to track structures having undergone multiple series of 
                transformations.
        """
        history = [] if history == None else history
        self._source = {}
        self._structures = []
        self._transformations = []
        self._redo_trans = []
        if len(history) > 0:
            self._source = history[0]
            for i in xrange(1, len(history)):
                self._structures.append(Structure.from_dict(history[i]['input_structure']))
                self._transformations.append(transformation_from_dict(history[i]))

        self._structures.append(structure)
        for t in transformations:
            self.append_transformation(t)

    def undo_last_transformation(self):
        """
        Undo the last transformation in the TransformedStructure.
        
        Raises:
            IndexError if already at the oldest change.
        """
        if len(self._transformations) == 0:
            raise IndexError("Can't undo. Already at oldest change.")
        self._structures.pop()
        self._redo_trans.append(self._transformations.pop())

    def redo_next_transformation(self):
        """
        Redo the last undone transformation in the TransformedStructure.
        
        Raises:
            IndexError if already at the latest change.
        """
        if len(self._redo_trans) == 0:
            raise IndexError("Can't undo. Already at latest change.")
        t = self._redo_trans.pop()
        self.append_transformation(t, False)

    def __getitem__(self, index):
        return (self._structures[index], self._transformations[0:index])

    def __len__(self):
        return len(self._structures)

    def append_transformation(self, transformation, clear_redo = True):
        """
        Appends a transformation to the TransformedStructure.
        
        Arguments:
            transformation:
                Transformation to append
            clear_redo:
                Boolean indicating whether to clear the redo list. By default,
                this is True, meaning any appends clears the history of undoing.
                However, when using append_transformation to do a redo, the redo
                list should not be cleared to allow multiple redos.
        """
        new_s = transformation.apply_transformation(self._structures[-1])
        self._structures.append(new_s)
        self._transformations.append(transformation)
        if clear_redo:
            self._redo_trans = []

    def extend_transformations(self, transformations):
        """
        Extends a sequence of transformations to the TransformedStructure.
        
        Arguments:
            transformations:
                Sequence of Transformations
        """
        for t in transformations:
            self.append_transformation(t)

    def get_vasp_input(self, vasp_input_set, generate_potcar = True):
        """
        Returns VASP input as a dict of vaspio objects.
        
        Args:
            vasp_input_set:
                pymatgen.io.vaspio_set.VaspInputSet like object that creates
                vasp input files from structures
            generate_potcar:
                Set to False to generate a POTCAR.spec file instead of a POTCAR,
                which contains the POTCAR labels but not the actual POTCAR. Defaults
                to True.
        """
        d = vasp_input_set.get_all_vasp_input(self._structures[-1], generate_potcar)
        d['transformations.json'] = json.dumps(self.to_dict)
        return d

    def write_vasp_input(self, vasp_input_set, output_dir, create_directory = True):
        """
        Writes VASP input to an output_dir.
        
        Args:
            vasp_input_set:
                pymatgen.io.vaspio_set.VaspInputSet like object that creates vasp input files from structures
            output_dir:
                Directory to output files
            create_directory:
                Create the directory if not present. Defaults to True.
        """
        vasp_input_set.write_input(self._structures[-1], output_dir, make_dir_if_not_present = create_directory)
        with open(os.path.join(output_dir, 'transformations.json'), 'w') as fp:
            json.dump(self.to_dict, fp)

    def __str__(self):
        output = ["Current structure"]
        output.append("------------")
        output.append(str(self._structures[-1]))
        output.append("\nSource")
        output.append("------------")
        output.append(str(self._source))
        output.append("\nTransformation history")
        output.append("------------")
        for t in self._transformations:
            output.append(str(t.to_dict))
        return "\n".join(output)

    @property
    def structures(self):
        """
        Returns a copy of all structures in the TransformedStructure. A structure
        is stored after every single transformation.
        """
        return [s for s in self._structures]

    @property
    def transformations(self):
        """
        Returns a copy of all transformations in the TransformedStructure. 
        """
        return [t for t in self._transformations]

    @property
    def final_structure(self):
        """
        Returns the final structure in the TransformedStructure.
        """
        return self._structures[-1]

    @staticmethod
    def from_dict(d):
        """
        Creates a TransformedStructure from a dict.
        """
        s = Structure.from_dict(d)
        return TransformedStructure(s, [], d['history'])

    @property
    def to_dict(self):
        """
        Returns a dict representation of the TransformedStructure.
        """
        d = self._structures[-1].to_dict
        history = [self._source]
        for i, t in enumerate(self._transformations):
            tdict = t.to_dict
            tdict['input_structure'] = self._structures[i].to_dict
            history.append(tdict)
        d['history'] = history
        d['version'] = __version__
        return d
    
class TransformedStructureTree(object):
    """
    Container object for groups of structures that include history of transformations. This is used for generating
    multiple output structures for a single or multiple input structures through transformations that have multiple
    outputs
    
    Each structure is stored as a transformed structure. Transformations that produce multiple output structures
    increase the number of structures in the tree. A pruning method removes duplicate structures from the tree.
    Care must be used to ensure that the tree doesn't get too big
    """

    def __init__(self, structures_list, transformations, histories = None):
        """
        Standard constructor for a TransformedStructureTree
        
        Args:
            structures_list:
                input structures (must be a list)
            transformations:
                sequence of transformations to be applied to the input structures.
            histories:
                optional history list for the input structures, which provides a way
                to track structures having undergone multiple series of 
                transformations. Must be the same length as structures_list
        """
        self._transformed_structures = []
        
        if histories:
            if not len(structures_list) == len(histories):
                raise ValueError("histories must have same length as structures_list")
            for i in range(len(structures_list)):
                self._transformed_structures.append(TransformedStructure(structures_list[i], transformations, histories[i]))
        else:
            for i in range(len(structures_list)):
                self._transformed_structures.append(TransformedStructure(structures_list[i], transformations, None))

    def undo_last_transformation(self):
        """
        Undo the last transformation in the TransformedStructure.
        
        Raises:
            IndexError if already at the oldest change.
        """
        for x in self._transformed_structures:
            x.undo_last_transformation()

    def redo_next_transformation(self):
        """
        Redo the last undone transformation in the TransformedStructure.
        
        Raises:
            IndexError if already at the latest change.
        """
        for x in self._transformed_structures:
            x.redo_next_transformation()

    def __getitem__(self, index):
        return [x.__getitem__(self, index) for x in self._transformed_structures]

    def __len__(self):
        return len(self._transformed_structures)

    def append_transformation(self, transformation, clear_redo = True):
        """
        Appends a transformation to the TransformedStructure.
        
        Arguments:
            transformation:
                Transformation to append
            clear_redo:
                Boolean indicating whether to clear the redo list. By default,
                this is True, meaning any appends clears the history of undoing.
                However, when using append_transformation to do a redo, the redo
                list should not be cleared to allow multiple redos.
        """
        new_transformed_structures = []
        structures_to_delete = []
        for x in self._transformed_structures:
            new_structs = transformation.apply_transformation(x.final_structure)
            if isinstance(new_structs, Iterable):
                structures_to_delete.append(x)
                for new_struct in new_structs:
                    new_tstruct = x
                    new_tstruct._structures.append(new_struct)
                    new_tstruct._transformations.append(transformation)
                    new_transformed_structures.append(new_tstruct)
            else:
                x._structures.append(new_structs)
                x._transformations.append(transformation)
            if clear_redo:
                x._redo_trans = []
        for x in structures_to_delete:
            self._transformed_structures.remove(x)
        self._transformed_structures.extend(new_transformed_structures)
                    

    def extend_transformations(self, transformations):
        """
        Extends a sequence of transformations to the TransformedStructure.
        
        Arguments:
            transformations:
                Sequence of Transformations
        """
        for t in transformations:
            self.append_transformation(t)

    def get_vasp_input(self, vasp_input_set, generate_potcar = True):
        """
        Returns VASP input as a dict of vaspio objects.
        
        Args:
            vasp_input_set:
                pymatgen.io.vaspio_set.VaspInputSet like object that creates
                vasp input files from structures
            generate_potcar:
                Set to False to generate a POTCAR.spec file instead of a POTCAR,
                which contains the POTCAR labels but not the actual POTCAR. Defaults
                to True.
        """
        return [x.__getitem__(self, vasp_input_set, generate_potcar) for x in self._transformed_structures]

    def write_vasp_input(self, vasp_input_set, output_dir, create_directory = True):
        """
        Writes VASP input to an output_dir.
        
        Args:
            vasp_input_set:
                pymatgen.io.vaspio_set.VaspInputSet like object that creates vasp input files from structures
            output_dir:
                Directory to output files
            create_directory:
                Create the directory if not present. Defaults to True.
        """
        vasp_input_set.write_input(self._structures[-1], output_dir, make_dir_if_not_present = create_directory)
        with open(os.path.join(output_dir, 'transformations.json'), 'w') as fp:
            json.dump(self.to_dict, fp)

    def __str__(self):
        output = ["Current structures"]
        output.append("------------")
        for x in self._transformed_structures:
            output.append(str(x._structures[-1]))
        return "\n".join(output)

#TODO: Code these following methods
'''
    @property
    def structures(self):
        """
        Returns a copy of all structures in the TransformedStructure. A structure
        is stored after every single transformation.
        """
        return [s for s in self._structures]

    @property
    def transformations(self):
        """
        Returns a copy of all transformations in the TransformedStructure. 
        """
        return [t for t in self._transformations]

    @property
    def final_structure(self):
        """
        Returns the final structure in the TransformedStructure.
        """
        return self._structures[-1]

    @staticmethod
    def from_dict(d):
        """
        Creates a TransformedStructure from a dict.
        """
        s = Structure.from_dict(d)
        return TransformedStructure(s, [], d['history'])

    @property
    def to_dict(self):
        """
        Returns a dict representation of the TransformedStructure.
        """
        d = self._structures[-1].to_dict
        history = [self._source]
        for i, t in enumerate(self._transformations):
            tdict = t.to_dict
            tdict['input_structure'] = self._structures[i].to_dict
            history.append(tdict)
        d['history'] = history
        d['version'] = __version__
        return d'''


class CifTransformedStructure(TransformedStructure):
    """
    Extended version of TransformedStructure to generates new materials from cifs.
    """

    def __init__(self, cif_string, transformations, primitive = True):
        """
        Args:
            cif_string:
                Input cif string. Should contain only one structure. For cifs
                containing multiple structures, please use CifTransmuter.
            transformations:
                Sequence of transformations to be applied to the input structure.
            primitive:
                Option to set if the primitive cell should be extracted. Defaults
                to True. However, there are certain instances where you might want
                to use a non-primitive cell, e.g., if you are trying to generate
                all possible orderings of partial removals or order a disordered
                structure.
        """
        parser = CifParser.from_string(cif_string)
        raw_string = re.sub("'", "\"", cif_string)
        cif_dict = parser.to_dict
        cif_keys = cif_dict.keys()
        s = parser.get_structures(primitive)[0]
        partial_cif = cif_dict[cif_keys[0]]
        if '_database_code_ICSD' in partial_cif:
            source = partial_cif['_database_code_ICSD'] + "-ICSD"
        else:
            source = 'uploaded cif'
        source_info = {'source':source, 'datetime':str(datetime.datetime.utcnow()), 'original_file':raw_string, 'cif_data':cif_dict[cif_keys[0]]}
        super(CifTransformedStructure, self).__init__(s, transformations, [source_info])


class PoscarTransformedStructure(TransformedStructure):
    """
    Generates a transformed structure from Poscar.
    """

    def __init__(self, poscar_string, transformations):
        """
        Args:
            poscar_string:
                Input POSCAR string.
            transformations:
                Sequence of transformations to be applied to the input structure.
        """
        p = Poscar.from_string(poscar_string)
        if not p.true_names:
            raise ValueError("Transformation can be craeted only from POSCAR strings with proper VASP5 element symbols.")
        raw_string = re.sub("'", "\"", poscar_string)
        s = p.struct
        source_info = {'source': "uploaded POSCAR", 'datetime':str(datetime.datetime.utcnow()), 'original_file':raw_string}
        super(PoscarTransformedStructure, self).__init__(s, transformations, [source_info])

