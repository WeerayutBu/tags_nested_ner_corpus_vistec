from attacut import tokenize, Tokenizer
import re
import numpy as np
import json 

def remove_pipe(json_clean_data, ssg_text, clean_text ):
    # replace text json file
    json_data = json.dumps(json_clean_data)
    json_data = json.loads(json_data)
    json_data['text'] = clean_text

    # Get index 
    list_idx = [(idx) for idx, c in enumerate(ssg_text) if c =='|']
    list_idx.append(len(ssg_text))
    list_pair_idx = [(i+1, list_idx[i], list_idx[i+1]+1) for i in range(len(list_idx)-1)]

    # Shift index
    json_data['entities'] = shift_index(json_data['entities'], list_pair_idx)
    return json_data

def check_sentence(data, text=None):
    data = json.dumps(data)
    data = json.loads(data)
    
    cl_text = data['text']
    en_list = data['entities']
    
    if( text is None ):
        text = cl_text
    
    Format = '{:<70} \t\t{:<20} {:<3}{:>5} <-> {:<20}'
    print('Text:\n\t{}\n'.format(text))
    print(Format.format('\ntext', 'type', 'No', 'start_idx', 'end_idx\n'))
    en_list = sorted(en_list, key=lambda x:(x['start_idx'], -x['end_idx']))
    
    for idx,entity in enumerate(en_list):
        print(Format.format(entity['text'], entity['type'], idx, entity['start_idx'], entity['end_idx']), end=' ')
        if(text != None ):
            check_text = text[int(entity['start_idx']):int(entity['end_idx'])]
            print('--{}--'.format(check_text),end='')
            print()
    print('\n All entities : ',idx+1,'\n')
    
def get_all_entities_index(entities):
    entities = sorted(entities, key=lambda x:(x['start_idx'], -x['end_idx']))
    SetS = set([element['start_idx'] for element in entities])
    SetE = set([element['end_idx'] for element in entities])
    return set.union(SetS, SetE)

def token_en2words(set_index, txt_test_data):
    # Dumps and load json data
    txt_test_data      = json.dumps(txt_test_data)
    txt_test_data      = json.loads(txt_test_data)
    temp               = 0
    save_token         = []
    
    for idx, _ in enumerate(range(len(txt_test_data))):
        
        # Tokenize entities
        if idx in set_index:
            e_token = txt_test_data[temp:idx]

            #Check empty text
            if(len(e_token) > 0):
                
                # Tokenize each sentence
                words_tokenize = tokenize(e_token)
                save_token.extend(words_tokenize)
                temp = idx
                
    save_token.extend(tokenize(txt_test_data[temp:]))
    return save_token

def update_idx(Idx_EN, shift_list):
    for shift, l, u in shift_list:
        if Idx_EN  in list(range(l, u)):
            return shift
    return 0

def shift_index(enitities, shift_list):
    enitities = json.dumps(enitities)
    enitities = json.loads(enitities)
    
    for idx,entity in enumerate(enitities):
        enitities[idx]['type']       = '_'.join(entity['type'].strip().split())
        enitities[idx]['start_idx'] -= update_idx(entity['start_idx'], shift_list)
        enitities[idx]['end_idx']   -= update_idx(entity['end_idx'], shift_list)
    return enitities

def tags_nested(words_token, entities, max_levels, group = False):
    
    entities            = sorted(entities, key=lambda x:(x['start_idx'], -x['end_idx']))
#     [print('{:<20} {:<10} {:<10}'.format(e['type'], e['start_idx'], e['end_idx'])) for e in entities]
    
    entities_type        = [e['type']      for e in entities]
    start_idx_ens        = [e['start_idx'] for e in entities]
    end_idx_ens          = [e['end_idx']   for e in entities]
    words_tags           = []
    Dict_entities        = {}
    temp_start, temp_end = 0, 0
    
    start_word_idx       = 0
    end_word_idx         = 0
    
    for idx_word, word in enumerate(words_token):
        start_word_idx = end_word_idx
        end_word_idx   = start_word_idx + len(word)
        
        # Push the entity into a dictionary when the start entity equal to start words token character index.
        if( start_word_idx in start_idx_ens):
            match_start_idx = np.where(np.array(start_idx_ens) == start_word_idx)[0]
#             if(len(match_start_idx) >= 2): print('Warning: There exist more than two entities in the same start position.')
            for idx_m in match_start_idx:
                type_en_math    = entities[idx_m]['type']
                type_en_math    = '_'.join(type_en_math.split('-'))
                Dict_entities.update({idx_m:type_en_math})
                
        if( group == True ):            
            # Assign the nested tags for each word.
            words_tags.append((word,[ grouptags(stk_en) for stk_en in Dict_entities.items()]))
        else:
            # Assign the nested tags for each word.
            words_tags.append((word,[stk_en for stk_en in Dict_entities.items()]))
        
        # Pop the entity into a dictionary when the end entity equal to end words token character index.
        if (end_word_idx in end_idx_ens):
            match_end_idx = np.where(np.array(end_idx_ens) == end_word_idx)[0]
#             if(len(match_end_idx) >= 2): print('Warning: There exist more than two entities in the same end position.')
            for idx_m in match_end_idx:
                type_en_math = entities[idx_m]['type']
                try:     del Dict_entities[idx_m]
                except:  print('Error !!! You are trying to pop emtry entitiy')
        else: pass
    
    # Add O tags
    nested_tags = []
    for word in words_tags:
        w = str(word[0]).strip()
#         print("{:<20} \t|".format(w), end='')

        nested_tag = []
        for i in range(max_levels):
            try    : tag = np.array(word[1])[i][0]+'-'+np.array(word[1])[i][1]
            except : tag = 'O'
                
            nested_tag.append(tag)  

        nested_tags.append((w,'|'.join(nested_tag)))
#         print()
    
    return nested_tags

def tags_bioes(words_tags, max_levels):
    level_tags = 1
    words_tags.insert(0,               ('start','|'.join(['X' for x in range(max_levels)])))
    words_tags.insert(len(words_tags), ('end',  '|'.join(['X' for x in range(max_levels)])))
    nested_tags_sent = []
    for wi in range(len(words_tags)-2):
        temp_word = []
        word      = words_tags[wi+1][0]
        temp_word.append(word)
    #     print('{:<20} \t'.format(str(word)),end=' : ')
        for wl in range(max_levels): 
            t1       = words_tags[wi][1].split('|')[wl]
            t2       = words_tags[wi+1][1].split('|')[wl]
            t3       = words_tags[wi+2][1].split('|')[wl]
            tag      = tags_entity(t1, t2, t3)

            if(tag != 'O'):
                tag = tag+'-'+t2.split('-')[1]

            temp_word.append(tag)
    #         print('{:<20}'.format(tag), end='|')
        nested_tags_sent.append(temp_word)
    #     [print('{:<20} \t'.format(t), end='|') for t in temp_word]
    #     print()
    words_tags.pop(0)
    words_tags.pop(-1)
    return nested_tags_sent

def transitionl1(t1,t2):
    x1 = '*'
    if  ( t2 == 'O'): x1 = 'O'
    elif( t2 == 'X'): x1 = 'X'
    elif( t1 != t2 ): x1 = 'S'
    elif( t1 == t2 ): x1 = 'I'
    else: print('Error !!! transitionl1 : 1') 
    return x1

def transitionl2(x1, x2):
    x = '**'
    if(x1 == 'S'):
        if  ( x2 in ['S', 'O', 'X']):  x = 'S'
        elif( x2 == 'I'):        x = 'B'
        else: print('Error !!! transitionl2 : 1')  
    elif(x1 == 'I'):
        if  ( x2 in ['S', 'O', 'X']):  x = 'E'
        elif( x2 == 'I'):              x = 'I'    
        else: print('Error !!! transitionl2 : 2')
    elif(x1 == 'O'):                   x = 'O'
    elif(x1 == 'X'):                   x = 'X'
    else: print('Error !!! transitionl2 : 3')
    return x
    
def tags_entity(t1,t2,t3):
    x  = '-'
    x1 = transitionl1(t1, t2)
    x2 = transitionl1(t2, t3)
#     print('Level 1 :',x1, x2)
    
    x  = transitionl2(x1, x2)
#     print('Level 2 :', x)
    return x

def save_data(datas, file, nested=False):
    for data in datas:
        if( nested == True):
            data = '|'.join(data)
        file.writelines(str(data)+'\n')
    file.writelines('\n')
    
def grouptags(tag):
    maintags = '''{
                    "Person"       : ["person", "title", "firstname", "middle", "last", "nicknametitle", "nickname", "namemod", "psudoname", "role"],
                    "Location"     : ["restaurant", "continent", "country" , "state", "city" , "district", "province", "sub_district", "roadname" , "address", "soi", "latitude", "longtitude" , "postcode", "ocean", "island", "mountian", "river", "space", "loc:others"],
                    "Time"         : ["date", "year", "month", "day", "time", "duration", "periodic" , "season", "rel"],
                    "Organisation" : ["orgcorp", "org:edu", "org:political", "org:religious", "org:other", "goverment", "army", "sports_team", "media", "hotel", "museum", "hospital", "band", "jargon", "stock_exchange", "index", "fund"],
                    "NORP"         : ["nationality", "religion", "norp:political", "norp:others"],
                    "Facility"     : ["airport", "port", "bridge", "building", "stadium", "station", "facility:other"],
                    "Event"        : ["sports_event","concert","natural_disaster","war","event:others"],
                    "WOA"          : ["book", "film", "song", "tv_show", "woa"],
                    "MISC"         : ["animate", "game", "language", "law", "award", "electronics", "weapon", "vehicle", "disease", "god", "sciname", "food:ingredient", "product:food", "product:drug", "animal_species"],
                    "NUM"          : ["cardinal" , "mult", "fold", "money" , "energy", "speed", "distance", "weight", "quantity", "percent", "temperature", "unit"]
                }'''
    
    maintag  = 'UNK'
    maintags  = json.loads(maintags)
    idx_tag = list(tag)[0]
    tag     = list(tag)[1]
    
    # Mapping sub-tags to main-tags
    for main in maintags.items():
        if tag in main[1]:
            maintag = main[0].lower()
            break
            
        elif tag == 'O':
            maintag = tag
            break
            
        else : continue
    
    if(maintag == 'UNK'):
        print(tag, "Error !!!: The tag doesn't match the main-tags.")
    return (idx_tag,maintag)
