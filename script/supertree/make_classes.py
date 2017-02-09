#!/usr/bin/env python

'''
Author: Astrid Blaauw
Date: 16/01/2016

Script to process table file, containing studies linked to species,
from here we trace every class from every species
(with help of the NCBI taxonomy).

Pipeline study_species table input:
    study_ID species_count species_ID(,species_ID)

Class table output:
	class_ID species_count study_count study_ID(, study_ID)
	...
	supported_class_ID_count
	unsupported_class_ID_count

Usage:
    -i  Text file containing study_ID's linked to species_ID list
    -t  NCBI taxdmp nodes file
    -n 	NCBI names files
'''

import argparse
import itertools
import os
import sys
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def proc_log(logmessage, logtype, log_file):
	if logtype == "inf":
		logging.info(logmessage)
		log_file.write("INFO: " + logmessage + "\n")
	if logtype == "war":
		logging.warning(logmessage)
		log_file.write("WARNING: " + logmessage + "\n")


class TaxNode:
	'''NCBI node class'''

	def __init__(self, taxid, parentid, rank):
		self.taxid = taxid
		self.parentid = parentid
		self.rank = rank

	def get_taxid(self):
		return self.taxid

	def get_parentid(self):
		return self.parentid

	def get_rank(self):
		return self.rank


def get_dict(table):
	'''
	Input:
		File name, for table -
		study_ID species_count species_ID(,species_ID)
	Output:
		dict {study_id : [species_count, [species_ID, species_ID]] }
	'''
	table_file = open(table)
	species = dict()
	for l in table_file:
		l = l.split()
		study_id = l[0]
		if len(l) < 3:
			species_list = [l[1], ["1"]]
		else:
			species_list = [l[1], l[2].split(",")]
		species[study_id] = species_list
	table_file.close()
	return(species)

def get_nodes_objects(nodedmp):
	'''
	Input:
		NCBI nodes.dmp
	Output:
		dict {node_id : node_object}
	'''
	nodes_file = open(nodedmp)
	nodes = dict()
	for i in nodes_file:
		line = i.split("|")
		node_id = line[0].strip()
		parent_id = line[1].strip()
		rank = line[2].strip()
		nodes[node_id] = TaxNode(node_id, parent_id, rank)
	nodes_file.close()
	return nodes

def get_names_dict(namedmp):
	'''
	Input:
		NCBI names.dmp
	Output:
		dict {node_id : tax_name}
	'''
	names_file = open(namedmp)
	names = dict()
	for i in names_file:
		line = i.split("|")
		node_id = line[0].strip()
		tax_name = line[1].strip()
		if node_id not in names:
			names[node_id] = tax_name
	names_file.close()
	return names

def main():

	parser = argparse.ArgumentParser(description='Process commandline arguments')
	parser.add_argument("-i", type=str,
    	                help="Input file (*.dat file from pipeline, containing MRP matrix/matrices)")
	parser.add_argument("-t", type=str,
    	                help="NCBI taxdmp nodes file")
	parser.add_argument("-n", type=str,
    	                help="NCBI names file")
	args = parser.parse_args()
	
	#outname_log = args.o + args.i
	#outname_log = outname_log.replace(".dat", ".log")
	#log_file = open(outname_log, "a")

	species_dict = get_dict(args.i)		
	unique_species = list()

	classes_table = dict()
	classes_table["none"] = [0, list()]
	
	nodes = get_nodes_objects(args.t)
	names = get_names_dict(args.n)
	names["none"] = "None"

	for n in nodes:
		n = nodes[n]
		if n.get_rank() == "class":
			nid = n.get_taxid()
			classes_table[nid] = [0, list()]

	for study in species_dict:	
		#logmessage = "processing " + study
		#logging.info(logmessage)

		# trace back every species ID to class level
		species_list = species_dict[study][1]
		species_count = species_dict[study][0]
		hits = 0
		for nid in species_list:
			if nid not in unique_species:
				unique_species.append(nid)
			while nid != "1":
				study = study.split("/")[-1]
				# check if targeted class taxon is found
				if (nid in classes_table.keys()) and (study not in classes_table[nid][1]):
					hits += 1
					classes_table[nid][1].append(study)
				nid = nodes[nid].get_parentid()
		if hits == 0:
			study = study.split("/")[-1]
			classes_table["none"][1].append(study)

	species_count = 0
	for nid in unique_species:
		species_count += 1
		while nid != "1":
			# check if targeted class taxon is found
			if nid in classes_table.keys():
				classes_table[nid][0] += species_count
				species_count = 0
			nid = nodes[nid].get_parentid()	
		classes_table["none"][0] += species_count
		species_count = 0
	
	hit = 0
	nohit = 0
	nameoccur = dict()
	for cid in classes_table:
		species_count = classes_table[cid][0]
		studies_list = classes_table[cid][1]
		if len(studies_list) > 0:
			hit += 1
			classname = names[cid].replace('"', "")
			classname = classname.replace(" ", "_")
			if classname not in nameoccur:
				nameoccur[classname] = 1
			else:
				nameoccur[classname] += 1
				classname = classname + "_" + str(nameoccur[classname])
			print(classname + "\t" + str(species_count) + "\t" + str(len(studies_list)) 
				+ "\t" + str(studies_list).replace("'", "")[1:-1] )
		else:
			nohit += 1
	print(str(hit))
	print(str(nohit))

	#log_file.close()

if __name__ == "__main__":
	main()