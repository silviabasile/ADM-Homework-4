
# coding: utf-8

# In[1]:


import html
import json
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sb
sb.set_style('darkgrid')
from itertools import combinations
import heapq
import random
from matplotlib import pylab
from collections import defaultdict


# In[2]:


def convert_names(data):
    '''This function converts all the author names with special characters in 
    readble names using the function "html.unescape".
    Input: the whole dataset
    Output: the same dataset with converted names
    '''
    #convert names
    for publ in data:
        for author in range(len(publ['authors'])):
            publ['authors'][author]['author'] = html.unescape(publ['authors'][author]['author'])
    return data


# #### Authors' dict

# In[3]:


#Create a dictionary with keys=(author,author_id) and values=(id_publication_int)
#The keys are each author with his given id and the values are the publication for each one
def create_dict(data):
    '''This function creates a dictionary with keys=(author,author_id) and values=(id_publication_int)
    Input: the dataset
    Output: the authors' dictionary
    '''
    authors={}
    for publ in data:
        for author in range(len(publ['authors'])):
            author_id=publ['authors'][author]['author_id']
            author_name = html.unescape(publ['authors'][author]['author'])
            if (author_name,author_id) in authors:
                authors[(author_name,author_id)].add(publ['id_publication_int'])    
            else:
                authors[(author_name,author_id)] = {publ['id_publication_int']}
    return authors


# #### Jaccard

# In[4]:


def jaccard(G, author, next_author):
    ''' This function evaluates the jaccard similarity between 
    the set of publication of two authors.
    Input: two authors id
    Output: the jaccard similarity
    '''
    intersection = len(G.node[author]['publications'].intersection(G.node[next_author]['publications']))
    union = len(G.node[author]['publications'].union(G.node[next_author]['publications']))
    jaccard = intersection / union
    return jaccard


# #### Graph

# In[5]:


def create_graph(data, authors):
    '''Given the authors' dictionary the function creates a graph in which
    each author is a node and two authors are linkes if they share at least 
    one publication.
    Input: the whole dataset and the authors' dict
    Output: the graph
    '''
    G = nx.Graph()
    #add nodes 
    for author in authors.keys():
        G.add_node(author[1], id=author[1], publications= authors[author], author_name=author[0])
    for pub in data:
        id_lst = [(x['author'], x['author_id']) for x in pub['authors']] #put id of authors in a list
        for coppia in combinations(id_lst,2):
            #add edges
            G.add_edge(coppia[0][1], coppia[1][1], weight = 1 - jaccard(G, coppia[0][1], coppia[1][1]))
    return G


# #### Subgraph given a conference

# In[6]:


def sub_conference_nodes(conference_id, data):
    '''This functions returns the list of all authors who published
    at the input conference at least once.
    Input: the id of the conference and the initial dictionary
    Output: the list of interested authors(nodes)'''
    author_sublist=[]
    for publication in data:
        if publication['id_conference_int'] == conference_id:
            for a in publication['authors']:
                author_sublist.append(a['author_id'])
    return set(author_sublist)


# #### Subgraph given an author id and a distance d

# In[7]:


def sub_authors_nodes(G, author_id, distance):
    '''This function creates a dictionary called 'visited' in
    which there are d keys representing the hop distances and the values are all the nodes that have
    hop distance equal to that key. 
    The dictionary is initialize as follows: at hop distance 0 there is hust the author id given in input
    and at hop distance 1 there are all the neighbors of it.
    The function returns a list of all interested nodes (without repetitions) taken from the 
    dictionary values. 
    Input: the graph, an author id and an integer representing the distance
    Output: the list of interesetd author ids
    '''
    # create dict
    visited = {0 : set([author_id]), 1: set(G.neighbors(author_id))}
    for k in range(2, distance+1):
        visited[k] = set()
    temporary = visited[1]
    
    i = 2
    while i <= distance:
        for node in temporary:
            visited[i].update(G.neighbors(node))
        temporary = visited[i]
        visited[i] = visited[i] - visited[i].intersection(visited[i-1])
        i += 1
    
    # create list of interested authors(nodes)
    nodes_list = set()
    for v in visited.values():
        nodes_list.update(v)
    nodes_list = list(nodes_list)
    
    return nodes_list


# #### Dijsktra

# In[8]:


def dijkstra(G, start, end):
    '''
    This function evaluates the distance of the shortest path using Dijkstra algorithm.
    The function does not works if the author ids given in input are not in the graph or if they are not connected.
    Moreover, it uses the *heap* data structure to keep track of the visited nodes and of their distances.

    Input: the graph and two author ids (the starting node and the final node).
    
    Output: a tuple in which the first element is the distance of the shortest path
    and the second element is a list of all nodes involved to go from the starting node to the final node.
    '''
    # Check whether the two nodes are in the graph
    # Keep the checks separated so that we know which one we have to modify
    if start not in G.nodes():
        return("The start node is not in the graph.")
    if end not in G.nodes():
        return("The end node is not in the graph.")
    
    # Check whether there is no path between the start and end nodes:
    # if end is in the nodes of the subgraph induced by start 
    if end not in nx.node_connected_component(G, start):
        return("There is no path between the start and end nodes.")
    
    # heapq object, list of tuples with (dist/cost, node)
    q = [(0, start, [])]
    # set of unseen nodes
    seen = set()
    
    while q:
        # dist and node of the closest node (closest to the previously seen node)
        dist, current, path = heapq.heappop(q)
        
        if current not in seen:
            # update the seen set
            seen.add(current)
            # update the path
            path = path + [current]
            # return if I found it
            if current == end:
                return (dist, path)
            # all current neighbors
            temp = G[current]
            # all unseen (not-visited) neighbors of current
            to_see = list(set(temp).difference(seen))
            
            # list of tuples with (updated-dist, node)
            # where node is one of the unseen neighbors and updated-dist is the distance from start to the node
            neigh = [(dist+temp[n]["weight"], n) for n in to_see]
            
            # add the new info ()
            for d, n in neigh:
                heapq.heappush(q, (d, n, path))


# #### Group Number

# In[9]:


def group_number(G, I):
    '''This function evaluates the shortest path between each node of
    the graph and each node of the subset I and returns the minimum among them.
    Input: the graph G and a subset of nodes I
    Output: a dictionary in which keys = nodes, values = group number.
    The dictionary contains only the nodes connected with the nodes in the subset.
    '''
    group = {}
    for graph_node in G.nodes():
        #inizialize the minimum with infinite
        min_path = [float('inf')]
        for sub_node in I :
            new_path = dijkstra(G, graph_node, sub_node)
            if type(new_path[0]) == float and new_path[0] < min_path[0]:
                min_path = new_path
        if type(new_path[0]) == float:
            group[graph_node] = min_path
            #print('The GroupNumber of the node %s is %s' %(graph_node, min_path))
    return group

