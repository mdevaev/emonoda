# -*- coding: utf-8 -*-


import os


##### Public methods #####
def onWalkError(exception) :
	raise exception

def treeList(dir_path, on_walk_error = onWalkError) :
	tree_files_list = []
	for (root, dirs_list, files_list) in os.walk(dir_path, onerror=on_walk_error) :
		for item in dirs_list + files_list :
			tree_files_list.append(os.path.join(root, item))
	return tree_files_list

