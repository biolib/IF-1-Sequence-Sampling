from Bio.PDB import PDBParser, PDBIO, Select
from Bio.PDB import MMCIFParser
from Bio.PDB.mmcifio import MMCIFIO

class NonHetSelect(Select):
    def accept_residue(self, residue):
        return 1 if residue.id[0] == " " else 0

    def save_new_pdb(self, pdb_file):
        if pdb_file.endswith(".pdb"):
            pdb_id = pdb_file.split('.')[0]
            pdb = PDBParser().get_structure(pdb_id, pdb_file)
            io = PDBIO()
            io.set_structure(pdb)
            io.save(f"non_het_{pdb_file}", NonHetSelect())
        elif pdb_file.endswith(".cif"):
            pdb_id = pdb_file.split('.')[0]
            pdb =  MMCIFParser().get_structure(pdb_id, pdb_file)
            io = MMCIFIO()
            io.set_structure(pdb)
            io.save(f"non_het_{pdb_file}", NonHetSelect())