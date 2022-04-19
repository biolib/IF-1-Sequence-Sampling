import argparse
import numpy as np
import pandas as pandas
from pathlib import Path
import torch
import torch.nn.functional as F
from tqdm import tqdm
from biotite.sequence.io.fasta import FastaFile, get_sequences
import os

import esm


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
    args = parser.parse_args()

    os.mkdir('output')

    model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()

    coords, seq = esm.inverse_folding.util.load_coords(args.pdbfile, args.chain)
    print('Sequence loaded from file:')
    print(seq)

    if args.score:
        seq_dict = {}

    with open('output/sampled_seqs.fasta', 'w') as f:
        for i in range(args.num_samples):
            print(f'\nSampling sequences... ({i+1} of {args.num_samples})')
            sampled_seq = model.sample(coords, temperature=args.temperature)
            print('Sampled sequence:')
            print(sampled_seq)
            f.write(f'>sampled_seq_{i+1}\n')
            f.write(sampled_seq + '\n')
            if args.score:
                seq_dict[f'sampled_seq_{i+1}'] = sampled_seq 

            recovery = np.mean([(a==b) for a, b in zip(seq, sampled_seq)])
            print('Sequence recovery:', recovery)

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

        output_file = open('output/output.md', 'w')

        df = pandas.read_csv('output/sampled_seqs_scored.csv')
        print("\n\nSampled Sequences Log Likelihood:", file=output_file)
        print(df.to_markdown(), file=output_file)

        best_sequence_idx = df[['log_likelihood']].idxmax()
        best_sequence_id = df['seqid'][best_sequence_idx].iloc[0]

        print(f'\nBest sequence is {best_sequence_id}', file=output_file)
        print(seq_dict[best_sequence_id], file=output_file)


if __name__ == '__main__':
    main()