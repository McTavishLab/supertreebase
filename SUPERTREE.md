How to run the TNT pipeline, the nasty bits
===========================================

The file [script/supertree/Makefile](https://github.com/TreeBASE/supertreebase/blob/master/script/supertree/Makefile) 
contains the steps for downloading TreeBASE data and preparing it for input into TNT. Below follows a discussion of
these steps, identified as make targets. 

If you want to work your way through these steps one by one, you would issue them in the order given, and you would do 
that inside the folder where the Makefile resides, i.e. in `script/supertree`. Most of the action will take place 
inside `data/treebase`. 

If you want to live dangerously you would simply get rid of the stale sitemap.xml (`make sitemap_clean`, if desired), 
and issue the last target (`make -j 4 tntscript`). However, this will almost certainly not work, for example because 
of failing downloads. 

A number of steps can be parallelized by make, by providing the `-j $num` command to specify the number of cores to 
run on. To revert any steps, issue the target as `make <target>_clean` (example: `make sitemap_clean` deletes the
sitemap.xml):

- `sitemap` - downloads the [sitemap.xml](http://treebase.org/treebase-web/sitemap.xml) from the TreeBASE website,
which lists all the studies currently published. The URLs are not pretty PURLs but URLs that directly compose the
query strings for the web application.
- `purls` - parses the sitemap.xml and extracts each URL, turning it into a PURL that points to the NeXML data
associated with the study. This means that inside `data/treebase` very many *.url files will be created: one for
each study. If a *.url file already exists it will be left alone, allowing for incremental downloads.
- `studies` - for every *.url file, downloads the NeXML file it points to. Again, this can be done incrementally
as make checks for the existence of target files (and their timestamps: if any *.url file is newer than a NeXML
file, a download is initiated, if the NeXML is newer than the URL, make assumes the target has been built and it
will leave well alone). _Some downloads fail (for a variety of reasons, e.g. the output is too much for
the web app to generate without timeouts). To get past this step you can create empty *.xml files, e.g. for 
study ID $foo, do `touch data/treebase/$foo.xml`_
- `tb2mrp_taxa` - for each *.xml file, creates a *.txt file with multiple MRP matrices: one for each tree block in
the study. The *.txt file is tab separated, structured thusly: $treeBlockID, "\t", $ncbiTaxonID, "\t", $mrpString, "\n".
Note that at this point, $ncbiTaxonID can be anything: a (sub)species, genus, family, whatever.
- `taxa` - creates a file `taxa.txt` with two data columns: "\s+", $occurrenceCount, "\s+", $ncbiTaxonID, "\n"
- `species` - creates a file `species.txt` that maps the $ncbiTaxonID's to species IDs. The logic is as follows: if 
$ncbiTaxonID is below species level (e.g. subspecies), collapse up to species level. If $ncbiTaxonID is above species
level, expand it to include all the species _that are seen to be subtended by that taxon in any TreeBASE study_. So we
don't simply include all species in the NCBI taxonomy, just the ones TreeBASE knows about.
- `tb2mrp_species` - for each study MRP file (*.txt) maps the $ncbiTaxonID to the species ID. Results in a *.dat
file for every MRP *.txt file. _Note: the list of *.xml/*.txt/*.dat files is constructed by make from the list
of *.url files generated out of the sitemap. Other files with the *.txt extension (such as species.txt) are ignored._
- `ncbi` - downloads and extracts the NCBI taxonomy flat files into `data/taxdmp`
- `ncbimrp` - builds an MRP matrix for the species that occur in TreeBASE. _Note: this MRP matrix is not actually being
used further, so this target is a dead end for now._
- `ncbicon` - builds TNT constraint commands based on the NCBI common tree for the TreeBASE species.
- `tntdata` - for each tree block in a *.dat file, creates a *.tnt file with the MRP matrix for that tree block, in TNT
syntax. So, for $study.dat creates $study.dat.$treeBlock1.tnt, $study.dat.$treeBlock2.tnt, and so on. Also creates 
for each *.dat file, a *.run file that contains the file inclusion commands (TNT syntax) to pull in all the MRP
matrices for a given study.
- `tntscript` - creates a file `tntscript.runall` thath combines all the file inclusion commands from `tntdata` into a 
single file.

How to run TNT, the loose ends
------------------------------

So, in the end there is a `tntscript.runall` that contains a long list of file inclusion commands. Each inclusion command
pulls in the MRP matrix for a single tree block in study. The rows in each MRP matrix are NCBI species identifiers.
For the actual analysis in TNT there is the script [tntwrap](https://github.com/TreeBASE/supertreebase/tree/master/data/treebase/tntwrap). Here are some thoughs and
experiences with this:
- The first step in that script is to increase RAM. On the Naturalis workstation there is enough RAM to load all the data. 
TNT gives an indication for how much RAM it would need - but that's only for the data itself, not for any trees. 
It appears that we need much more RAM than TNT suggests.
- TNT has some non-standard facility for parallel searches (not based on MPI or OpenMP), which involves the `ptnt`
command. I never got this to work properly.
- I also never got the commands that I cribbed from DOI:10.1111/j.1096-0031.2009.00255.x to work as advertised. Someone
with a fairly intimate knowledge of the TNT language is going to have to deal with this. I guess in principle it's
only a couple of lines of code that should go in the `tntwrap` but I can't figure it out.
