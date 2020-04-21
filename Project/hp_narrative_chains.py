'''
	hp_narrative_schemas.py

	Objective: Extract Narrative Chains of each of the HP Charaters from the Fan Fiction and the Canon.

	Inspiration:	Chambers and Jurafsky, 2008 -  Unsupervised learning of Narrative Event Chains{https://www.aclweb.org/anthology/P08-1090.pdf}
					Chambers and jurafsky, 2009 - Unsupervised Learning of Narrative Schemas and their Participants{https://www.aclweb.org/anthology/P09-1068.pdf}

	Methods:	get_word_to_sentence_mapping_locations(dependency_parses, chapter_num, story)
				get_corrected_indices(orig_doc, coref_doc)
                get_cluster_num_to_NNP_map(clusters, coref_doc)
                get_sentences_replaced_with_clusters(original_document, original_sentences, words_to_sentence_locations, sentence_starting_positions, clusters, coref_document)
				get_narrative_chains_from_dep_parsing(dependency_parses, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs)
				get_narrative_chains_from_sem_roles(semantic_roles, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs)
                run_hpff_chains(filename)
                hpff_analysis(narrative_chains, is_dp_chains=True, with_clusters=True)

    Folders:    code/
                data/
                out/
                vectors/

    Usage:  python hp_narrative_schemas.py <HPFF_FILENAME> <HPCANON_FILENAME>
    Example:python hp_narrative_schemas.py HPFF-small.json HPCanon-full.json	

    Output files:   'hpff_dp_narrative_chains_with_cluster_nums.txt'
                    'hpff_dp_narrative_chains_with_NNPs.txt'
                    'hpff_sr_narrative_chains_with_cluster_nums.txt'
                    'hpff_sr_narrative_chains_with_NNPs.txt'
                    'hpff_dp_narrative_chains_counts_clusters.txt'
                    'hpff_dp_narrative_chains_counts_NNPs.txt'
                    'hpff_sr_narrative_chains_counts_clusters.txt'
                    'hpff_sr_narrative_chains_counts_NNPs.txt'					
'''

import collections
from collections import *
import json
import os, sys
import codecs
import pickle as pkl
import nltk 
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize, sent_tokenize 
stop_words = set(stopwords.words('english'))

import util
# import analyze_HPFF
# import NLP_analysis

baseDir = '/Users/rebeccaflores/Documents/GitHub/IFaTG/Final_Project/data/'

def get_word_to_sentence_mapping_locations(dependency_parses, chapter_num, story):
    '''
        Input: Dependency Parses for each chapter.  Dependency parses are done at the sentence level
        Return: original_document - chapter level tokenized words for the document from the dependency parser
                original_sentence - the original sentence level tokenized words (a list of list, where each list in the tokenized sentence out of a chapter)
                words_to_sentence_locations - all the words are mapped to an index of the sentence it's located in
                sentence_starting_positions - maps to the index of the word of where each sentence starts
                Returning a chapter level dependency parse to use for coreference resolution and word to sentence mappings
    '''

    original_document = []
    original_sentences = []
    # compute the word offsets for each sentence.
    word_offset = 0
    # record what sentence each word is in
    words_to_sentence_locations = [] 
    sentence_starting_positions = []
    for sent_num, dep_parse in enumerate(dependency_parses):
        dep_parse['word_offset'] = word_offset
        words = dep_parse['words']
        sentence_starting_positions.append(word_offset)
        word_offset += len(words) 
        original_sentences.append(words)
        for i in range(len(words)):
            words_to_sentence_locations.append(sent_num)
            original_document.append(words[i]) ## appending sentence level words as if it were appended at the chapter level
        # print('sentence_starting_positions: ', sentence_starting_positions)
        # print('word_offset: ', word_offset)
        # print('original_sentences: ', original_sentences)
        # print('words_to_sentence_locations: ', words_to_sentence_locations)
        # print('original_document: ', original_document)
    story['chapters'][chapter_num]['words_to_sentence_locations'] = words_to_sentence_locations

    return original_document, original_sentences, words_to_sentence_locations, sentence_starting_positions, story


# Some of the words in the co-ref document are blank, which causes
# alignment problems with the words  in the original document. 
'''
    said another way:
    most of the problems occur from the fact that we have to replace
    coreference clusters with the right entity at the sentence level, 
    but the cluster references are given at the chapter level.  So we
    have to correct the alignment of the clusters in the coref document
    to match where it actually should be replaced at the sentence level.
'''

def get_corrected_indices(orig_doc, coref_doc):
    '''
        Input: orig_doc, coref doc
        Output: For every Chapter, coref_document (at the chapter level) is corrected to adapt to the sentence level, so mentions can
                be replaced correctly in the original dep parse sentence level document.  You need sentence level replacement of the cluster
                mention because it needs to correspond to other tools from dep parse that are also done at the sentence level.
    '''

    j = 0
    corrected_indices = []
    for i in range(len(coref_doc)):
        corrected_indices.append(j-i)
        if coref_doc[i].strip() != '':
    #    print("'%s', '%s'" % (original_doc[j].strip(), coref_doc[i].strip()))
            if orig_doc[j] != coref_doc[i]:
                print('\n\n')
                print('problematic words: ', orig_doc[j], coref_doc[i] )
                print('*************')
                print("Mismatch starting at ", i)
                print(orig_doc[j+1], coref_doc[i+1])
                print('*************')
                print('\n\n')
                # break
            j += 1

    return corrected_indices

def get_cluster_num_to_NNP_map(clusters, coref_doc):
    '''
        Input: the clusters and its associated coref_document for the chapter.  
               Each iterations through the story chapters has a new cluster to proper noun map.  This index map will be used to resolve the 
               nodes later on for event sequencing in get_narrative_chains_from_dep_parsing() and get_narrative_chains_from_sem_roles().  But
               first they correct prounoun for that cluster needs to be replaced at each mention in the document in get_sentences_replaced_with_clusters().
        Output: An index map where the key is the cluster num and the value is it's associated proper noun
    '''
    
    document = []
    for i in range(len(coref_doc)):
        document.extend([coref_doc[i].strip()])

    cluster_num_to_NNP_dict = defaultdict(lambda:[])
    filtered_cluster_num_to_NNP_dict = defaultdict()
    target_tags = ['NNP', 'NN','NNS', 'VB', 'VBD', 'VBP', 'PRP$', 'PRP']

    for cluster_num, cluster in enumerate(clusters):
        mentions = []
        for [i, j] in cluster:
            #print(i, '\t', j, '\t', " ".join(document[i:j+1]))
            mention = " ".join(document[i:j+1])
            mentions.append(mention)
        # print(cluster_num, ":", ", ".join(mentions))
        cluster_num_to_NNP_dict[cluster_num].extend(mentions)

    # print('this is the dict after the first pass')
    # for key, val in cluster_num_to_NNP_dict.items():
    #     print(key, '\t', val)

    for cluster, mentions in cluster_num_to_NNP_dict.items():

        filtered_mentions = [x for x in mentions if x != '' and x != ' ']
        tagged = nltk.pos_tag(filtered_mentions)
        names = [x for (x,y) in tagged]
        pos_tags = [y for (x,y) in tagged]
        matches = [i for i in range(len(pos_tags)) if pos_tags[i] in target_tags]
 
        if matches:

            name = ''
            counts = defaultdict(lambda:Counter())
            for name, tag in zip(names,pos_tags):
                counts[tag].update([name])

            check = None
            for tag in target_tags:
                check = counts[tag]
                if not check:
                    continue
                else:
                    name = counts[tag].most_common(1)[0][0]
                    break

            if check == None or not check:
                filtered_cluster_num_to_NNP_dict[cluster] = "COREF_CLUSTER_" + str(cluster)
            else:
                filtered_cluster_num_to_NNP_dict[cluster] = name

        else:

            filtered_cluster_num_to_NNP_dict[cluster] = "COREF_CLUSTER_" + str(cluster)

    # print('This is the final dictionary map on line 193:')
    # for key,val in filtered_cluster_num_to_NNP_dict.items():
    #     print(key, '\t', val)
    return filtered_cluster_num_to_NNP_dict

def get_sentences_replaced_with_clusters(original_document, original_sentences, words_to_sentence_locations, sentence_starting_positions, clusters, coref_document):
    '''
        Input: original_document, original_sentences, words to sentence mappings, sentence starting positions, clusters, coref_document
        Output: Find where the coref_doc is inconsistent (sometimes they add extra spaces in the tokenization of the document)
                Correct the indices from the coref_document to match the correct-indices from the original document (from dependency parsing)
                Then, that's mapped to the words_to_sentence locations to replace the clusters at the sentence level
                Cluster references replace the characters they refer to at the sentence level
    '''
    # print('\n\n')
    # print('*************')
    # print('this is what the clusters look like: ')
    # for cluster in clusters:
    #     print(cluster)
    # print('len of coref document: ', len(coref_document))
    # print('example of whole coref document: ', coref_document)
    # print('*************')
    # print('\n\n')
    import copy

    corrected_indices = get_corrected_indices(original_document, coref_document)
    cluster_num_to_NNP_map = get_cluster_num_to_NNP_map(clusters, coref_document)

    doc_replaced_with_cluster_nums = copy.deepcopy(original_document) ## tokenized words created from the sentence level tokens appended into chapter level tokens
    doc_replaced_with_NNPs = copy.deepcopy(original_document)
    sentences_replaced_with_cluster_nums = copy.deepcopy(original_sentences) ## original sentence level lists of the chapter, tokenized words created from the sentence level tokens appended into chapter level tokens
    sentences_replaced_with_NNPs = copy.deepcopy(original_sentences)

    corrected_spans = []
    for cluster_num, cluster in enumerate(clusters):

        possible_entities = cluster_num_to_NNP_map[cluster_num]

        
        ## for every span in the cluster
        for [i, j] in cluster:

            corrected_i = i + corrected_indices[i]
            corrected_j = j + corrected_indices[j]

            ## where the actual clusters should be replaced in the coref document
            corrected_spans.append([corrected_i, corrected_j])

            for position_in_doc in range(corrected_i, corrected_j+1):


                ## document level replacements in you need
                doc_replaced_with_cluster_nums[position_in_doc] =  "COREF_CLUSTER_" + str(cluster_num)
                doc_replaced_with_NNPs[position_in_doc] = cluster_num_to_NNP_map[cluster_num]

                # Below is the sentence level replacements and the logic explained at each step
                '''
                    1. Get the sentence position of the span we're on [i,j]
                    2. Retrieve the actual sentence from the deepcopy of the original sentences
                    3. Get the word position from the sentence position of the span we're on
                    4. Replace that span in the sentence (in this case, all words associated in that span) with the cluster we're on
                '''

                curr_sentence_location_of_this_word = words_to_sentence_locations[position_in_doc]

                sentence_with_clusters = sentences_replaced_with_cluster_nums[curr_sentence_location_of_this_word] ## sentence level replacements
                sentence_with_NNPs = sentences_replaced_with_NNPs[curr_sentence_location_of_this_word] ## sentence level replacements

                position_of_word_in_the_sentence = position_in_doc - sentence_starting_positions[curr_sentence_location_of_this_word]

                sentence_with_clusters[position_of_word_in_the_sentence] = "COREF_CLUSTER_" + str(cluster_num)
                sentence_with_NNPs[position_of_word_in_the_sentence] = cluster_num_to_NNP_map[cluster_num]


    return sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs, doc_replaced_with_cluster_nums, doc_replaced_with_NNPs

def get_narrative_chains_from_dep_parsing(dependency_parses, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs):
    '''
        Input: dependency_parses and sentences_replaced_with_cluster_nums from coref resolution.  
        Return: Event extraction for this chapter
    ''' 

    narrative_chains_with_clusters = []
    narrative_chains_with_NNPs = []
    target_tags = ['nn','nsubj', 'nsubjpass','amod', 'advcl','poss', 'conj', 'dobj'] ##['nn''nsubj', 'poss','admod', 'advcl'] maybe take out 'root' later
    # problematic_sents = ["\"ME??!!", "\"No!", "\"NO!", "-Flashback-"]
    # words = []

    for dep_parse, curr_sent_with_clusters, curr_sent_with_NNPs in zip(dependency_parses, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs):

        modified_words = ["<root>"] + curr_sent_with_clusters  ## dep_parse['words'] 
        orig_words = ["<root>"] + curr_sent_with_NNPs
        dependencies = ["<root>"] + dep_parse['predicted_dependencies']
        if len(dep_parse['predicted_dependencies']) == 0:
            print('there are no predicted dependencies for: ', modified_words)
        predicted_heads = [-1] + dep_parse['predicted_heads']
        # print('curr_sentence:\t' , modified_words)
        # print('current deps:\t', dependencies)
        # print('current heads:\t', predicted_heads)
 
        curr_chain_with_clusters = []
        curr_chain_with_NNPs = []
        check_entities = []
        for curr_head_i in range(1, len(dependencies)):

            if dependencies[curr_head_i] in target_tags:

                father_i = predicted_heads[curr_head_i]
                grandfather_i = predicted_heads[father_i]

                try:
                    modified_words[curr_head_i]
                except IndexError:
                    print('tuple index out of range')
                    print(len(modified_words), modified_words)
                    print(curr_head_i)
                    print(father_i)
                    print(grandfather_i)
                    continue

                check_entities.append(curr_head_i-1)
                curr_chain_with_clusters.append((
                                     (curr_head_i-1, father_i-1, grandfather_i-1), 
                                     (modified_words[curr_head_i], dependencies[curr_head_i]),
                                     (modified_words[father_i], dependencies[father_i]),
                                     (modified_words[grandfather_i], dependencies[grandfather_i])
                                    ))

                curr_chain_with_NNPs.append((
                                     (curr_head_i-1, father_i-1, grandfather_i-1), 
                                     (orig_words[curr_head_i], dependencies[curr_head_i]),
                                     (orig_words[father_i], dependencies[father_i]),
                                     (orig_words[grandfather_i], dependencies[grandfather_i])
                                    ))
      
        if len(check_entities) == 0 or len(curr_chain_with_clusters) == 0:
            # print('1) no entities to resolve!')
            continue

    # print('2) curr_chain_with_clusters: \t', curr_chain_with_clusters)
    if curr_chain_with_clusters:
        narrative_chains_with_clusters.append(curr_chain_with_clusters)
        narrative_chains_with_NNPs.append(curr_chain_with_NNPs)

    # print('3) narrative_chains_with_clusters:\t', narrative_chains_with_clusters)
    if not narrative_chains_with_clusters:
        # print('no target dependencies: ')
        # print(len(modified_words), modified_words)
        # print(len(orig_words), orig_words)
        # print(len(dependencies), dependencies)
        return ['<none>'], ['<none>']
    else:
        return narrative_chains_with_clusters, narrative_chains_with_NNPs

#for i, word in enumerate(original_document):
#  print(word, '\t', doc_replaced_with_cluster_nums[i])

def get_narrative_chains_from_sem_roles(semantic_roles, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs):
    '''
        Input: semantic_roles from nlp analysis and sentences_replaced_with_cluster_nums from coref resolution
        output: return semantic roles for this chapter
    ''' 

    for sentence, curr_sent_with_clusters, curr_sent_with_NNPs in zip(semantic_roles, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs):
        verbs = sentence['verbs']
        mod_words = curr_sent_with_clusters ## semantic_roles['words']
        orig_words = curr_sent_with_NNPs
        # print('verbs: ', verbs)
        # print('mod_words: ', mod_words)
        target_tags = ['B-ARG0', 'B-V', 'B-ARG1','ARGM-GOL'] ## 'I-ARG1', 

        narrative_chains_with_clusters = []
        narrative_chains_with_NNPs = []
        for verb in verbs:
            temp_with_clusters = []
            temp_with_NNPs =[]
            for i,tag in enumerate(verb['tags']):
                if tag in target_tags:
                    try:
                        temp_with_clusters.append((tag, mod_words[i]))
                        temp_with_NNPs.append((tag, orig_words[i]))
                    except IndexError:
                        print('\n\n')
                        print("Index mismatched:")
                        print('verb[\'tags\']: ', verb['tags'])
                        print('tag:', tag)
                        print('mod_words: ', mod_words, orig_words)
                        print('index: ', i)
                        print('\n\n')
                        continue
            if temp_with_clusters:
                narrative_chains_with_clusters.append(temp_with_clusters)
                narrative_chains_with_NNPs.append(temp_with_NNPs)

    return narrative_chains_with_clusters, narrative_chains_with_NNPs

def run_hpff_chains(filename): 
    '''
        Objective: Gather all the events from HPFF
        Return: to list objects for narrative events extracted using dep parse and sem role labeling separately
                both files are written to pickle files.
    '''
    import gzip
    json_nlp_filename = filename

    dp_narrative_chains_with_cluster_nums = []
    dp_narrative_chains_with_NNPs = []
    sr_narrative_chains_with_cluster_nums = []
    sr_narrative_chains_with_NNPs = []

    with gzip.open(json_nlp_filename) as json_file:
        for idx, line in enumerate(json_file):
            try:
                story = json.loads(line)
            except json.decoder.JSONDecodeError:
                print('You\'ve got a json error! i.e. - Extra data: line 1 column 292980 (char 292979)')
                print('line:\t%d\tlength of line: %d' % (idx,len(line)))
                print('type: ', type(line))
                continue
            ## chapter level
            for chapter in story['chapters']:
                try:
                    dependency_parses = story['chapters'][chapter]['nlp']['dependency_parses'] ## dependecy parses are at the sentence level
                    clusters = story['chapters'][chapter]['nlp']['coref']['clusters'] ## clusters are at the chapter level
                    coref_document = story['chapters'][chapter]['nlp']['coref']['document'] ## document is at the chapter level.  It's one single list of tokenized words - including punctuation - at the chapter level
                    semantic_roles = story['chapters'][chapter]['nlp']['semantic_roles']
                    original_document, original_sentences, words_to_sentence_locations, sentence_starting_positions, story = get_word_to_sentence_mapping_locations(dependency_parses, chapter, story)
                    sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs, document_replaced_with_cluster_nums, document_replaced_with_NNPs = get_sentences_replaced_with_clusters(original_document, original_sentences, words_to_sentence_locations, sentence_starting_positions, clusters, coref_document)

                    ## events based off dependency parsing
                    dp_chapter_chains_with_clusters, dp_chapter_chains_with_NNPs = get_narrative_chains_from_dep_parsing(dependency_parses, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs)
                    dp_narrative_chains_with_cluster_nums.extend(dp_chapter_chains_with_clusters)
                    dp_narrative_chains_with_NNPs.extend(dp_chapter_chains_with_NNPs)
                    
                    ## events based off semantic role labeling
                    sr_chapter_chains_with_clusters, sr_chapter_chains_with_NNPs = get_narrative_chains_from_sem_roles(semantic_roles, sentences_replaced_with_cluster_nums, sentences_replaced_with_NNPs)
                    sr_narrative_chains_with_cluster_nums.extend(sr_chapter_chains_with_clusters)
                    sr_narrative_chains_with_NNPs.extend(sr_chapter_chains_with_NNPs)

                except TypeError:
                    print('one of these values are emtpy! You are on chapter %s on story line %d and len(story[chapters]) %d' % (chapter, idx, len(story['chapters'])))
                    print('dep_parse: ', dependency_parses==None)
                    print('clusters: ', clusters==None)
                    print('coref_doc: ', coref_document==None)
                    print('sem_roles: ', semantic_roles==None)
                    print('story: ', story==None)
                    print('line: ', line==None)
                    print('story[chapters]', story['chapters']==None)
                    print('story[chapters][chapter]', story['chapters'][chapter]==None)
                    print('story[chapters][chapter][nlp]', story['chapters'][chapter]['nlp']==None)
                    print('story[chapters][chapter][nlp][coref]', story['chapters'][chapter]['nlp']['coref']==None)
                    continue

            print('Story %d successfully finished!' % (idx))

    print('length of dep_parse_narrative_chains using cluster nums: %d' % (len(dp_narrative_chains_with_cluster_nums))) ##819 changed to 379
    print('length of dep_parse_narrative_chains using NNPs: %d' % (len(dp_narrative_chains_with_NNPs))) ##819 changed to 379
    print('length of sem_role_narrative_chains using cluster nums: %d' % (len(sr_narrative_chains_with_cluster_nums))) ##872
    print('length of sem_role_narrative_chains using NNPs: %d' % (len(sr_narrative_chains_with_NNPs))) ##872


    return dp_narrative_chains_with_cluster_nums, dp_narrative_chains_with_NNPs, sr_narrative_chains_with_cluster_nums, sr_narrative_chains_with_NNPs 

def hpff_analysis(narrative_chains, is_dp_chains=True, with_clusters=True):
    '''
        Input:  narrative chains extracted either from dep parse or semantic roles.  The booleans is_dp_chains identifies
                whether the data was extracted from dep parse or semantic roles.  The boolean with_clusters identifies if
                the nodes are created with the cluster num of with the actual name of the entitiy
        Output: Return the narrative chains dependings on the different factors described in the input.
    '''

    # for chapter_num, chapter_chains in enumerate(narrative_chains[100:110]): 
    #     if chapter_chains == '<none>': 
    #         continue 
    #     for narrative_chain in chapter_chains: 
    #         print('\n') 
    #         print(len(narrative_chain), narrative_chain)

    narrative_chain_counts = defaultdict(lambda: [])

    if is_dp_chains:

        if with_clusters:

            for chapter_num, chapter_chains in enumerate(narrative_chains): 
                if chapter_chains == '<none>': 
                    continue 
                for narrative_chain in chapter_chains: 
                    # print('\n') 
                    # print(len(narrative_chain), narrative_chain)
                    cluster_mention = narrative_chain[1][0]
                    if cluster_mention.startswith('COREF_CLUSTER'):
                        narrative_chain_counts[cluster_mention].append(narrative_chain)

            return narrative_chain_counts

        else:

            for chapter_num, chapter_chains in enumerate(narrative_chains): 
                if chapter_chains == '<none>': 
                    continue 
                for narrative_chain in chapter_chains: 
                    # print('\n') 
                    # print(len(narrative_chain), narrative_chain)
                    cluster_mention = narrative_chain[1][0]
                    narrative_chain_counts[cluster_mention].append(narrative_chain)

            return narrative_chain_counts
    else:

        if with_clusters:

            for chain in narrative_chains:
                cluster_mention = chain[0][1]
                if cluster_mention.startswith('COREF_CLUSTER'):
                    narrative_chain_counts[cluster_mention].append(chain)

            return narrative_chain_counts 

        else:

            for chain in narrative_chains:
                cluster_mention = chain[0][1]
                narrative_chain_counts[cluster_mention].append(chain)

            return narrative_chain_counts



if __name__ == '__main__' :

    ## Load Data
    hpff_filename = sys.argv[1]
    # hpcanon_filename = sys.argv[2]


    ###################################################
    # HPFF
    ###################################################

    ## Get Narrative Chains
    hpff_dp_narrative_chains_with_cluster_nums, hpff_dp_narrative_chains_with_NNPs, hpff_sr_narrative_chains_with_cluster_nums, hpff_sr_narrative_chains_with_NNPs = run_hpff_chains(hpff_filename)
    util.pickle_dump(hpff_dp_narrative_chains_with_cluster_nums, 'hpff_dp_narrative_chains_with_cluster_nums.txt')
    util.pickle_dump(hpff_dp_narrative_chains_with_NNPs, 'hpff_dp_narrative_chains_with_NNPs.txt')
    util.pickle_dump(hpff_sr_narrative_chains_with_cluster_nums, 'hpff_sr_narrative_chains_with_cluster_nums.txt')
    util.pickle_dump(hpff_sr_narrative_chains_with_NNPs, 'hpff_sr_narrative_chains_with_NNPs.txt')
    # print(hpff_sr_narrative_chains_with_cluster_nums[100:110])
    # print(hpff_sr_narrative_chains_with_NNPs[100:110])
    print('Finished pickle dump...')
    
    ## Group Similar Narrative Chains Together
    hpff_dp_narrative_chains_counts_clusters = hpff_analysis(hpff_dp_narrative_chains_with_cluster_nums, True, True)
    hpff_dp_narrative_chains_counts_NNPs = hpff_analysis(hpff_dp_narrative_chains_with_NNPs, True, False)
    hpff_sr_narrative_chains_counts_clusters = hpff_analysis(hpff_sr_narrative_chains_with_cluster_nums, False, True)
    hpff_sr_narrative_chains_counts_NNPs = hpff_analysis(hpff_sr_narrative_chains_with_NNPs, False, False)
    util.write_json(hpff_dp_narrative_chains_counts_clusters,'hpff_dp_narrative_chains_counts_clusters.txt')
    util.write_json(hpff_dp_narrative_chains_counts_NNPs,'hpff_dp_narrative_chains_counts_NNPs.txt')
    util.write_json(hpff_sr_narrative_chains_counts_clusters, 'hpff_sr_narrative_chains_counts_clusters.txt')
    util.write_json(hpff_sr_narrative_chains_counts_NNPs, 'hpff_sr_narrative_chains_counts_NNPs.txt')
    print('Finished json dump...')
    

    # import util
    # data = util.load_json('hpff_dp_narrative_chains_counts_clusters.txt')
    #         # 'hpff_dp_narrative_chains_counts_NNPs.txt'
    #         # 'hpff_sr_narrative_chains_counts_clusters.txt'
    #         # 'hpff_sr_narrative_chains_counts_NNPs.txt'
    # for cluster, narrative_chains in data.items(): 
    #     print(cluster) 
    #     for chain in narrative_chains: 
    #         print(chain)
    print('Done Processing. Exiting...')

    ###################################################
    # HPCanon
    ###################################################

# Traceback (most recent call last):
#   File "hp_narrative_chains.py", line 510, in <module>
#     hpff_dp_narrative_chains_with_cluster_nums, hpff_dp_narrative_chains_with_NNPs, hpff_sr_narrative_chains_with_cluster_nums, hpff_sr_narrative_chains_with_NNPs = run_hpff_chains(hpff_filename)
#   File "hp_narrative_chains.py", line 401, in run_hpff_chains
#     story = json.loads(line)
#   File "/usr/lib64/python3.6/json/__init__.py", line 354, in loads
#     return _default_decoder.decode(s)
#   File "/usr/lib64/python3.6/json/decoder.py", line 342, in decode
#     raise JSONDecodeError("Extra data", s, end)
# json.decoder.JSONDecodeError: Extra data: line 1 column 292980 (char 292979)

# try:
#     story = json.loads(line)
#     print(type(story), type(line)
# except json.decoder.JSONDecodeError:
#     print('You\'ve got a json error!')
#     print(idx, len(line))
#     print(type(line))
#     exit()

# You've got a json error!
# 464 508840
# <class 'bytes'>

# stty: 'standard input': Inappropriate ioctl for device
# stty: 'standard input': Inappropriate ioctl for device
# Traceback (most recent call last):
#   File "hp_narrative_chains.py", line 515, in <module>
#     hpff_dp_narrative_chains_with_cluster_nums, hpff_dp_narrative_chains_with_NNPs, hpff_sr_narrative_chains_with_cluster_nums, hpff_sr_narrative_chains_with_NNPs = run_hpff_chains(hpff_filename)
#   File "hp_narrative_chains.py", line 411, in run_hpff_chains
#     clusters = story['chapters'][chapter]['nlp']['coref']['clusters'] ## clusters are at the chapter level
# TypeError: 'NoneType' object is not subscriptable
