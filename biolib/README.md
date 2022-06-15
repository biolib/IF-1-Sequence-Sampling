# Sequence Sampling with IF-1

Sequence sampling is the task of different generating sequences that fold to the same structure.

Given a structure we might want to generate sequences that could have more favorable residues. 

The sequences can also be scored by the model, the scores are the conditional log-likelihoods conditioned on the structure.

### Run from Python
This tool can also easily be run from Python with BioLib 🐍


```python
import biolib

sequence_sampler_if1 = biolib.load('Protein_Tools/Sequence_Sampler_IF1')
sampler_results = sequence_sampler_if1.cli(args='your_file.pdb --chain A --score')
sampler_results.save_files("your_results/")
```

We have also created a [python notebook](https://colab.research.google.com/drive/1ctFs0Gr6M05HTq3i4it5eI4ydL0jAcnL?usp=sharing) with an example. 


### About IF-1

IF-1 is a model that stacks a transformer on top of the GVP (Geometric Vector Perceptron).

The model has been trained on 12 million structures where all but ~16k of them are predicted structures.

### Acknowledgements

The IF-1 model was built by a team at Meta AI led by Chloe Hsu.

Please check out the implementation here:

https://github.com/facebookresearch/esm/tree/main/esm/inverse_folding


Please cite their amazing paper if using this application in research:

https://www.biorxiv.org/content/10.1101/2022.04.10.487779v1 