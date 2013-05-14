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

def treeListToDict(files_list) :
	tree_dict = {}
	for path in files_list :
		parts_list = os.path.normpath(path).split(os.path.sep)
		local_dict = tree_dict
		for (index, part) in enumerate(parts_list) :
			if index != 0 and len(part) == 0 :
				continue
			local_dict.setdefault(part, {})
			local_dict = local_dict[part]
	return tree_dict

