#!/usr/bin/env python


# Importing necessary packages

import pandas as pd

import numpy as np

import subprocess

import argparse

import matplotlib.pyplot as plt

import os

from help import *

import concurrent.futures as cf

from sklearn.linear_model import LinearRegression

from imgparser import SVGconstructor as constructor

# Adding parameters and a general help message

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=desctxt, add_help=False)

parser.add_argument('input', nargs='*')

parser.add_argument('-h', '--help', default=argparse.SUPPRESS)

parser.add_argument('-i', '--input', nargs='+', metavar='', dest='inputopt')

parser.add_argument('-a', '--annotation', default='F', choices=['T', 'F'])

parser.add_argument('-c', '--colors', nargs='+', default=['red', 'green'], type=str)

parser.add_argument('-t', '--threads', default=1, type=int)

parser.add_argument('-s', '--style', default=3, type=int)

parser.add_argument('-f', '--outfmt', default='svg', choices=['pdf', 'svg'], type=str)

parser.add_argument('-o', '--outdir', default='premirnaplot', type=str)

args = parser.parse_args()


# Parsing the arguments

inputs = args.inputopt if args.input == [] else args.input

if not inputs:
	print(desctxt)
	quit()

annot = True if args.annotation == 'T' else False

nthreads = args.threads

pdf = True if args.outfmt == 'pdf' else None

outdir = args.outdir

if len(args.colors) == 2:

	color1, color2 = args.colors

	if color1 not in defcolors or color2 not in defcolors:

		raise Exception("ERROR! One of the colors you informed is incorrect, please check your spelling or review the predefined colors.")

	else:
		color1, color2 = defcolors[color1], defcolors[color2]

elif len(args.colors) == 6:

	for color in args.colors:
		if int(color) < 0 or int(color) > 255:
			raise Exception("ERROR! Please use RGB code values between 0 and 255")

	color1 = "#{:02x}{:02x}{:02x}".format(int(args.colors[0]), int(args.colors[1]), int(args.colors[2]))
	color2 = "#{:02x}{:02x}{:02x}".format(int(args.colors[3]), int(args.colors[4]), int(args.colors[5]))

else:
	raise Exception("\nThere was an error checking the colors you provided, please review them")


filedata = {}

# Functions used in the program




def initial_check(filename):

	with open(filename) as arc:

		prelist = []

		for index, line in enumerate(arc.readlines()):

			line = line[:-1].upper().replace(' ', '').split('\t')

			if annot:

				annotation = line[0].lower()
				precursor = line[1].replace('N', '')
				mirna1 = line[2].replace('N', '')
				if len(line) == 4:
					mirna2 = line[3].replace('N', '')
				else:
					mirna2 = None
			else:
				precursor = line[0].replace('N', '')
				mirna1 = line[1].replace('N', '')
				if len(line) > 2:
					mirna2 = line[2].replace('N', '')

			mirname = annotation if annot else 'precursor_{}'.format(index)

			prelist.append(Precursor(mirname, precursor, mirna1, mirna2))

	filedata[filename] = prelist


def folding(prec):

	rnafold = subprocess.Popen('RNAfold ',  stdin=subprocess.PIPE,
											stdout=subprocess.PIPE,
											shell=True,
											universal_newlines=True,
											cwd='foldings/')

	alldata, _ = rnafold.communicate('>{}\n{}'.format(prec.name, prec.premirna))

	with open('foldings/{}_fold.txt'.format(prec.name), 'w') as dot:

		dot.write(alldata)
		prec.setpremfe(float(alldata.split(' ')[-1][1:-2]))

	prec.setpredsec(alldata.split('\n')[2].split(' ')[0])

	prec.mismatches()

	rnaplot = subprocess.Popen(['RNAplot -o svg --filename-full'],
																stdin=subprocess.PIPE,
																cwd='colored_structures/',
																shell=True,
																universal_newlines=True)

	rnaplot.communicate(alldata)

	constructor('colored_structures/' + prec.name + '_ss.svg', args.style, prec.pos1, prec.pos2, color1, color2, pdf=pdf)

	return prec


subprocess.run('mkdir {}/'.format(outdir), shell=True)


for file in inputs:

	filedata[file] = []

	print(f"#######  Checking if {file} is ok..\n")

	initial_check(file)

	print('\n#######  Data check complete for {}\n'.format(file))


for file in filedata:

	mfelst = []
	sizelst = []

	name = (file.split('/')[-1][:-4] if '.' in file else name)

	subprocess.run('mkdir {}/{} {}/{}/foldings {}/{}/colored_structures'.format(outdir, name, outdir, name, outdir, name), shell=True)

	os.chdir('{}/{}/'.format(outdir, name))

	data = pd.DataFrame({'Names':[]})

	with cf.ThreadPoolExecutor(max_workers=nthreads) as executor:

		for idx, precursor in enumerate(executor.map(folding, filedata[file])):

			print('# Created {} image'.format(precursor.name))

			fields = vars(precursor)

			params = {'name':'Names', 'premirna':'Precursor sequence', 'predsec':'Secondary structure', 'mirna1':'miRNA5p', 'mirna2':'miRNA3p', 'prelen':'Precursor length', 'premfe':'MFE', 'mfeden':'MFEden',
            			'duplexmm':'Duplex MM', 'mirna1mm':'miRNA5p mm', 'mirna2mm':'miRNA3p mm', 'gccontent':'''%GC''',  'mirna1gc':'''%GC miRNA5p''', 'mirna2gc':'''%GC miRNA3p''',}

			# data.loc[idx, 'Names'] = precursor.name
			# data.loc[idx, 'Precursor sequence'] = precursor.premirna
			# data.loc[idx, 'Secondary structure'] = precursor.predsec
			# data.loc[idx, 'miRNAs'] = ','.join(list(precursor.mirnas)) if len(list(precursor.mirnas)) == 2 else list(precursor.mirnas)[0]
			# data.loc[idx, 'Precursor length'] = precursor.prelen
			# data.loc[idx, 'MFE'] = precursor.premfe
			# data.loc[idx, 'MFEden'] = precursor.mfeden
			# data.loc[idx, 'Duplex mm'] = precursor.duplexmm
			# data.loc[idx, 'Mirna1 mm'] = precursor.mirna1mm
			# data.loc[idx, 'Mirna2 mm'] = precursor.mirna2mm
			# data.loc[idx, 'GC duplex'] = precursor.gccontent
			# data.loc[idx, 'GC mirna1'] = precursor.mirna1gc
			# data.loc[idx, 'GC mirna2'] = precursor.mirna2gc

			for param in params:
				
    				data.loc[idx, params[param]] = fields[param]
    
			for nt, freq in precursor.porcents().items():
				
				data.loc[idx, '%{}'.format(nt)] = freq

			for triplet, freq in precursor.triplets().items():
				
    				data.loc[idx, triplet] = freq

	data = data.set_index('Names')
	
	data.to_csv(path_or_buf='precursor_data.txt', sep='\t')

	plt.clf()
	plt.boxplot(data['Precursor length'])
	plt.title('Precursor length')
	plt.ylabel('Sequence length (nt)')
	plt.savefig('length.png', dpi=500)

	plt.clf()
	plt.boxplot(data['MFE'])
	plt.title('Predicted minimum free energy')
	plt.ylabel('Minimum free energy (kJ/mol)')
	plt.savefig('mfe.png', dpi=500)

	plt.clf()
	plt.scatter(data['Precursor length'], data['MFE'], edgecolors='black', color=color1, zorder=2)
	x = data['Precursor length'].values.reshape((-1, 1))
	y = data['MFE']
	model = LinearRegression().fit(x, y)
	plt.plot(x, model.predict(x), color='black', zorder=1)
	plt.rcParams.update({'font.size':8})
	plt.xlabel('Precursor length')
	plt.ylabel('Minimum free energy (kJ/mol)')
	plt.savefig('mfexlength.png', dpi=500)

	os.chdir('../../')
