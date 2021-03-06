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
from tqdm import tqdm
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
        '--score-fasta-file',
        help='score the given fasta file',
        type=str,
    )
    parser.add_argument(
            '--mask', 
            help='Mask part of the sequence. Eg: Mask from residue 10 to 15 and from residue 21 to 25: 10-15,21-25.'       
    )
    
    args = parser.parse_args()

    warnings.filterwarnings("ignore")
    os.mkdir('output')
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Pre-process the input file
    preprocess = NonHetSelect()
    preprocess.save_new_pdb(args.pdbfile)

    # New input file name
    pdbfile = f"non_het_{args.pdbfile}"
    #pdbfile = args.pdbfile

    # Load the model to GPU
    if args.score: print("Step 1/4 | Loading the ESM-IF1 model...")
    else: print("Step 1/3 | Loading the ESM-IF1 model...")
    
    model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
    with torch.no_grad():
        model.eval()
        model = model.cuda()

        # Load the file
        if args.score: print("Step 2/4 | Embedding the protein structure...")
        else: print("Step 2/3 | Embedding the protein structure...")
        # Their utilities are not working with cif files # TODO
        coords, seq = esm.inverse_folding.util.load_coords(pdbfile, args.chain)
        
        masked_seq = np.array(list(seq))
        if args.mask is not None:
            print("Masking option active, masking your sequence...")
            # Select the range for masking
            mask = args.mask.replace(" ", "").split(",")
            for m in mask:
                if m.find("-") != -1:
                    start = int(m.split('-')[0])
                    end = int(m.split('-')[-1])
                    # Asses too long mask span, if its 30 residues (so if 1-30, includes 1 and 30, this is why 29)
                    if end - start >= 29:
                            print(f"Warning! The mask span is longer than 30 residues, it can produce low performance results. \n\tStart of the mask: {start}\n\tEnd of the span: {end}\t")
                    # -1 because python lists start at 0
                    coords[start-1:end, :] = float('inf')
                    masked_seq[start-1:end] = "*" 
                    masked_seq[start-1:end] = "*" 
                    masked_seq[start-1:end] = "*" 
                else:
                    # For single numbers
                    start = int(m)
                    # -1 because python lists start at 0
                    coords[start-1, :] = float('inf')
                    masked_seq[start-1]= "*" 
                    masked_seq[start-1]= "*" 
                    masked_seq[start-1]= "*" 
                            
            
        print('Sequence loaded from file:')
        print(seq)
        
        if args.mask is not None: print(f"Your sequence was masked to:\n{''.join(masked_seq)}\n")
        
        output_file = open('output/output.md', 'w')

        
        if args.score:
            print("Step 3/4 | Start sampling...")
            seq_dict = {}
        elif args.score_fasta_file:
            print("Step 3/4 | Skipping sampling...")
            seq_dict = {}
        
        else: 
            print("Step 3/3 | Start sampling...")

        if not args.score_fasta_file:
            
            with open('output/sampled_seqs.fasta', 'w') as f:
                for i in range(args.num_samples):
                    print(f'\nSampling sequences... ({i+1} of {args.num_samples})')
                    sampled_seq = model.sample(coords, device, temperature=args.temperature)
                    print(f'Sequence: {sampled_seq}')
                    f.write(f'>sampled_seq_{i+1}\n')
                    f.write(sampled_seq + '\n')
                    if args.score:
                        seq_dict[f'sampled_seq_{i+1}'] = sampled_seq
                        recovery = np.mean([(a == b) for a, b in zip(seq, sampled_seq)])
                        print('Sequence recovery:', recovery)

            print("### Sequence sampler IF1 results\n", file=output_file)
            print("You can download the sampled sequences [here](sampled_seqs.fasta)\n", file=output_file)

        if args.score or args.score_fasta_file:
            print("Step 4/4 | Scoring sequences...")
            ll, _ = esm.inverse_folding.util.score_sequence(
                model, alphabet, coords, seq, device)
            print('\n\nNative sequence')
            print(f'Log likelihood: {ll:.2f}')
            print(f'Perplexity: {np.exp(-ll):.2f}')

            infile = FastaFile()
            if args.score_fasta_file:
                print(f'\nScoring sequences from provided sequence file {args.score_fasta_file}...\n')
                infile.read(args.score_fasta_file)
            else:
                print('\nScoring variant sequences from sequence file..\n')
                infile.read('output/sampled_seqs.fasta')

            seqs = get_sequences(infile)
            with open('output/sampled_seqs_scored.csv', 'w') as fout:
                fout.write('seqid,sequence,log_likelihood\n')
                for header, seq in tqdm(seqs.items()):
                    ll, _ = esm.inverse_folding.util.score_sequence(
                        model, alphabet, coords, str(seq), device)
                    fout.write(header.split()[0] + ',' + str(seq) + ',' + str(ll) + '\n')
                    if str(seq) not in seq_dict:
                        seq_dict[header.split()[0]] = str(seq)

            df = pandas.read_csv('output/sampled_seqs_scored.csv')
            print("You can download the scorings for the sequences [here](sampled_seqs_scored.csv) \n", file=output_file)
            print("\n\nSampled Sequences ranked by Log Likelihood:\n", file=output_file)
            df = df.sort_values(by=['log_likelihood'], ascending=True) 
            print(df.to_markdown(), file=output_file)

            best_sequence_idx = df[['log_likelihood']].idxmax()
            best_sequence_id = df['seqid'][best_sequence_idx].iloc[0]

            print(
                f'\n Highest scoring sequence is **{best_sequence_id}**:', file=output_file)
            print(f"```{seq_dict[best_sequence_id]}```", file=output_file)


if __name__ == '__main__':
    main()
