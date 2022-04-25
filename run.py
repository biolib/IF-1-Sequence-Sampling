from preprocess import NonHetSelect
import os
import warnings
import argparse
from pathlib import Path
from tqdm import tqdm

import numpy as np
import pandas as pandas

import torch
import torch.nn.functional as F

from biotite.sequence.io.fasta import FastaFile, get_sequences

import esm

# Pre-process module
import sys
sys.path.append('/')


def main():
    parser = argparse.ArgumentParser(
        description='Sample sequences based on a given structure.'
    )
    parser.add_argument(
        'pdbfile', type=str,
        help='input filepath, either .pdb or .cif',
    )
    parser.add_argument(
        '--chain', type=str,
        help='chain id for the chain of interest', default=None,
    )
    parser.add_argument(
        '--temperature', type=float,
        help='temperature for sampling, higher for more diversity',
        default=1.,
    )
    parser.add_argument(
        '--num-samples', type=int,
        help='number of sequences to sample',
        default=1,
    )
    parser.add_argument(
        '--score',
        help='score the sampled sequences',
        action='store_true',
    )
    parser.add_argument(
            '--mask', 
            help='Mask part of the sequence. Eg: Mask from residue 10 to 15 and from residue 21 to 25: 10-15,21-25.'       
    )
    
    args = parser.parse_args()

    warnings.filterwarnings("ignore")
    os.mkdir('output')

    # Pre-process the input file
    preprocess = NonHetSelect()
    preprocess.save_new_pdb(args.pdbfile)

    # New input file name
    pdbfile = f"non_het_{args.pdbfile}"
    #pdbfile = args.pdbfile

    # Load the model
    model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()

    # Load the file
    # Their utilities are not working with cif files # TODO
    coords, seq = esm.inverse_folding.util.load_coords(pdbfile, args.chain)
    if args.mask is not None:
        print("Masking option active, masking your sequence...")
        # Select the range for masking
        mask = args.mask.spli(",")
        for m in mask:
                start = m.split('-')[0]
                end = m.split('-')[-1]
                coords[start:end, :] = float('inf')
    print('Sequence loaded from file:')
    print(seq)

    if args.score:
        seq_dict = {}

    with open('output/sampled_seqs.fasta', 'w') as f:
        for i in range(args.num_samples):
            print(f'\nSampling sequences... ({i+1} of {args.num_samples})')
            sampled_seq = model.sample(coords, temperature=args.temperature)
            print(f'Sequence: {sampled_seq}')
            f.write(f'>sampled_seq_{i+1}\n')
            f.write(sampled_seq + '\n')
            if args.score:
                seq_dict[f'sampled_seq_{i+1}'] = sampled_seq

            recovery = np.mean([(a == b) for a, b in zip(seq, sampled_seq)])
            print('Sequence recovery:', recovery)

    output_file = open('output/output.md', 'w')
    print(
        "You can download the sampled sequences [here](sampled_seqs.fasta)\n", file=output_file)

    if args.score:
        ll, _ = esm.inverse_folding.util.score_sequence(
            model, alphabet, coords, seq)
        print('\n\nNative sequence')
        print(f'Log likelihood: {ll:.2f}')
        print(f'Perplexity: {np.exp(-ll):.2f}')

        print('\nScoring variant sequences from sequence file..\n')
        infile = FastaFile()
        infile.read('output/sampled_seqs.fasta')
        seqs = get_sequences(infile)
        with open('output/sampled_seqs_scored.csv', 'w') as fout:
            fout.write('seqid,log_likelihood\n')
            for header, seq in tqdm(seqs.items()):
                ll, _ = esm.inverse_folding.util.score_sequence(
                    model, alphabet, coords, str(seq))
                fout.write(header + ',' + str(ll) + '\n')

        df = pandas.read_csv('output/sampled_seqs_scored.csv')
        print(
            "You can download the scorings for the sequences [here](sampled_seqs_scored.csv) \n", file=output_file)
        print("\n\nSampled Sequences Log Likelihood:\n", file=output_file)
        print(df.to_markdown(), file=output_file)

        best_sequence_idx = df[['log_likelihood']].idxmax()
        best_sequence_id = df['seqid'][best_sequence_idx].iloc[0]

        print(
            f'\n Highest scoring sequence is **{best_sequence_id}**', file=output_file)
        print(seq_dict[best_sequence_id], file=output_file)


if __name__ == '__main__':
    main()
