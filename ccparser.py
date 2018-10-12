from __builtin__ import str
import platform
import os
import posixpath

class CloneTuple:
    def __init__(self, project_id, file_id):
        self.project_id = project_id
        self.file_id = file_id
        self.is_clone = False
        self.clone_set = set([self])
        
    def get_key(self):
        return (self.project_id,self.file_id)
    
    def add_path(self, file_path):
        self.file_path = file_path
        
    def add_tokens(self, tokens):
        self.tokens = tokens
        
    def __str__(self):
        return '%d,%d' % (self.project_id,self.file_id)
    
    def __cmp__(self, other):
        if hasattr(other,'project_id') and hasattr(other,'file_id'):
            res = self.project_id.__cmp__(other.project_id)
            if res == 0:
                res = self.file_id.__cmp__(other.file_id)
            return res
    
    def __hash__(self):
        return id(self)

class Ccparser:
    def __init__(self):
        self.clone_tuple_dict = dict()
        self.project_path_dict = dict()
        self.clone_set_list = []
        self.clone_set_sorted_list = []

    def load_project_list(self, file_name):
        with open(file_name) as f:
            i = 0
            for line in f:
                line = line.strip()
                i += 1
                self.project_path_dict[i] = line
                
    def load_file_stats(self, file_name):        
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                elems = line.split(',')
                pid = int(elems[0])
                fid = int(elems[1])
                t = self.find_tuple(pid,fid)
                p = elems[2].strip('"')
                if self.project_path_dict.get(pid) is not None:
                    project_path = self.project_path_dict[pid]
                    p = posixpath.relpath(p, project_path)
                t.add_path(p)
    
    def load_file_token(self, file_name):
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                elems = line.split(',')
                tokens = int(elems[2])
                pid = int(elems[0])
                fid = int(elems[1])
                t = self.find_tuple(pid,fid)
                t.add_tokens(tokens)
    
    def find_tuple(self, project_id, file_id):
        t = self.clone_tuple_dict.get((project_id, file_id))
        if t is None:
            t = CloneTuple(project_id,file_id)
            self.clone_tuple_dict[t.get_key()] = t
        return t
    
    def load_clone_pairs(self, file_name):
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                elems = line.split(',')
                pid = int(elems[0])
                fid = int(elems[1])
                t0 = self.find_tuple(pid,fid)
                pid = int(elems[2])
                fid = int(elems[3])
                t1 = self.find_tuple(pid,fid)
                t0.is_clone = True
                t1.is_clone = True
                                
                s0 = t0.clone_set
                s1 = t1.clone_set
                if s0 != s1:
                    s = s0 | s1
                    if s0 in self.clone_set_list:
                        self.clone_set_list.remove(s0)
                    if s1 in self.clone_set_list:    
                        self.clone_set_list.remove(s1)
                    self.clone_set_list.append(s)
                    for t in s:
                        t.clone_set = s                

    def save_clone_sets(self, file_name):
        with open(file_name,'w') as f:
            for s in self.clone_set_list:
                line = ''
                for t in s:
                    if line == '':
                        line = '%s' % str(t)
                    else:
                        line = '%s;%s' % (line,str(t))
                line = '%s\n' % line
                f.write(line)
                
    def save_clone_sets_sorted(self, file_name):
        with open(file_name,'w') as f:
            for s in self.clone_set_sorted_list:
                line = ''
                for t in s:
                    if line == '':
                        line = '%s' % str(t)
                    else:
                        line = '%s;%s' % (line,str(t))
                line = '%s\n' % line
                f.write(line)

    def load_clone_sets(self, file_name):
        with open(file_name) as f:
            for line in f:
                line = line.strip()
                elems = line.split(';')
                clone_set = set()
                for elem in elems:
                    e = elem.split(',')
                    pid = int(e[0])
                    fid = int(e[1])
                    t = self.find_tuple(pid,fid)
                    t.is_clone = True
                    clone_set.add(t)
                    t.clone_set = clone_set
                self.clone_set_list.append(clone_set)
    
    def clone_set_sort(self):
        for s in self.clone_set_list:
            l = sorted(list(s))
            self.clone_set_sorted_list.append(l)
        self.clone_set_sorted_list.sort(key = len, reverse=True)

    def file_stats_count(self):
        file_count = dict()
        for t in self.clone_tuple_dict.values():
            if file_count.get(t.project_id) is None:
                file_count[t.project_id] = 0
            file_count[t.project_id] += 1
        return file_count
    
    def clone_file_count(self):
        file_count = dict()
        for t in self.clone_tuple_dict.values():
            if t.is_clone == True:
                if file_count.get(t.project_id) is None:
                    file_count[t.project_id] = 0
                file_count[t.project_id] += 1
        return file_count
    
    def export_unclone_file(self, file_name, min_tokens = 0, max_tokens = 0):
        with open(file_name,'w') as f:
            l = self.clone_tuple_dict.values()
            l.sort()
            for t in l:
                if t.is_clone == False:
                    if (min_tokens > 0) and (t.tokens < min_tokens):
                        continue
                    if (max_tokens > 0) and (t.tokens > max_tokens):
                        continue
                    line = '%d:%s:%s\n'%(t.tokens, str(t), t.file_path)
                    f.write(line)
    
    def export_clone_set(self, file_name, clone_set_list):
        with open(file_name,'w') as f:
            i = 0
            for s in clone_set_list:
                i += 1
                j = 0
                for t in s:
                    j += 1
                    line = '%d,%d:%s:%s\n' % (i,j,str(t),t.file_path)
                    f.write(line)
                f.write('\n')
    
    def clone_filter_by_project(self, project_set):
        filter_list = []
        for s in self.clone_set_sorted_list:
            for t in s:
                if t.project_id in project_set :
                    filter_list.append(s)
                    break
        return filter_list         
    
    def export_project_tree(self, file_name, project_id):
        dir_dict = dict()
        for t in self.clone_tuple_dict.values():
            if t.project_id == project_id:          
                project_set = set()
                dirname = os.path.dirname(t.file_path)
                if dir_dict.get(dirname) is None:
                    dir_dict[dirname] = dict()
                    dir_dict[dirname][0] = 0
                dir_dict[dirname][0] +=1   
                for tt in t.clone_set:
                    if tt.project_id != project_id:
                        project_set.add(tt.project_id)

                for pid in project_set:
                    if dir_dict[dirname].get(pid) is None:
                        dir_dict[dirname][pid] = 0
                    dir_dict[dirname][pid] += 1                
        with open(file_name,'w') as f:
            dir_list = sorted(dir_dict.items(), key = lambda item:item[0])
            for (k,v) in dir_list:
                line = '%s:%s\n' % (k,v)
                f.write(line)
                
if __name__ == '__main__':
    sysstr = platform.system()
    if sysstr == "Windows":
        ccroot = os.path.abspath('D:/cc1') 
        project_root = os.path.abspath('D:/projects')
    else:
        ccroot = os.path.abspath('/media/bao/Tools/cc2')
        project_root = os.path.abspath('/media/bao/Tools/projects')
    fstats = os.path.join(ccroot, 'files_stats/files-stats-0.stats')   
    ftoken = os.path.join(ccroot, 'files_tokens/files-tokens-0.tokens')
    
    fproject_list = os.path.join(project_root, 'project-list.txt')    
    fpairs = os.path.join(ccroot, 'results.pairs')
    fsets = os.path.join(ccroot, 'clone_sets.txt')
    fsorted = os.path.join(ccroot, 'sorted.txt')
    funclone = os.path.join(ccroot, 'unclone.txt')
    fclones = os.path.join(ccroot, 'clones.txt')
    ffilter = os.path.join(ccroot, 'filter.txt')
    ftree = os.path.join(ccroot, 'tree.txt')

    parser = Ccparser()
    parser.load_project_list(fproject_list)
    parser.load_file_stats(fstats)
    parser.load_file_token(ftoken)
    
    if os.path.exists(fsets):
        parser.load_clone_sets(fsets)
    else :
        parser.load_clone_pairs(fpairs)
        parser.save_clone_sets(fsets)
    
    parser.clone_set_sort()
    if not os.path.exists(fsorted):        
        parser.save_clone_sets_sorted(fsorted)
    print parser.clone_file_count()
    print parser.file_stats_count()
    if not os.path.exists(funclone):
        parser.export_unclone_file(funclone,50,500000)
    if not os.path.exists(fclones):  
        parser.export_clone_set(fclones, parser.clone_set_sorted_list)
#     project_set = [26,27]
#     clone_set_list = parser.clone_filter_by_project(project_set)
#     parser.export_clone_set(ffilter, clone_set_list)
    parser.export_project_tree(ftree, 27)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    