import json

import h5py
import subprocess
from tqdm import tqdm
import numpy as np
import pandas as pd


def get_all_ctgs(h5pyfile):
	refs = h5pyfile.get('all_category_name').value[0]
	all_ctgs = []
	for ref in refs:
		ctg = ''.join([chr(c) for c in h5pyfile[ref].value])
		all_ctgs.append(ctg)
	return all_ctgs


def make_ctg_tsv(mat_file='./fashon_parsing_data.mat'):
	f = h5py.File(mat_file, 'r')
	all_ctgs = get_all_ctgs(f)

	# save
	sr = pd.Series(all_ctgs)
	sr.name = 'category'
	sr.index.name = 'category_id'
	sr.to_csv('./label/categories.tsv',
			  sep='\t', header=True)


def make_bbox_json(mat_file='./fashon_parsing_data.mat'):
	f = h5py.File(mat_file, 'r')
	all_ctgs = get_all_ctgs(f)
	iter_ = iter(f.get('#refs#').values())
	df = pd.DataFrame()
	for outfit in tqdm(iter_, total=len(f.get('#refs#'))):
		try:
			# super pix 2 category
			spix2ctg = outfit.get('category_label').value[0]
			#pd.Series(spix2ctg).value_counts().plot(kind='bar')

			# img_name
			ascii_codes = list(outfit.get('img_name').value[:,0])
			img_name = ''.join([chr(code) for code in ascii_codes ])

			# super pix
			spixseg = outfit.get('segmentation').value.T
			#plt.imshow(spixseg)

			# super pix -> semantic segmentation
			semseg = np.zeros(spixseg.shape)
			for i, c in enumerate(spix2ctg):
				semseg[spixseg == i] = c-1

			# semseg -> bbox
			items = []
			for i, ctg in enumerate(all_ctgs):
				region = np.argwhere(semseg == i)
				if region.size != 0:
					bbox = {
						'ymin':int(region.min(0)[0]),
						'xmin':int(region.min(0)[1]),
						'ymax':int(region.max(0)[0]),
						'xmax':int(region.max(0)[1]),
					}
					items.append({
						'bbox': bbox,
						'category': ctg,
					})

			df = df.append({
				'img_name': img_name,
				'items': items,
			}, ignore_index=True)
		except AttributeError:
			pass

	d = df.to_dict(orient='records')
	with open('./label/bbox.json', 'w') as f:
		json.dump(d, f, indent=4)


if __name__=='__main__':
	subprocess.call(['mkdir', 'label'])
	make_ctg_tsv()
	make_bbox_json()