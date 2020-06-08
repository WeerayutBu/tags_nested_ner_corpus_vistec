import json

def remove_pipe(tags_ne, data_csv_ssg, text_clean_csv):
    # Start Clean data
    clean_data = json.dumps(tags_ne)
    clean_data = json.loads(clean_data)
    
    for json_clean_data, ssg_text, clean_text in zip(clean_data, data_csv_ssg, text_clean_csv):
        
        # replace text json file
        json_clean_data['text'] = clean_text
        
        # Get index 
        list_idx = [(idx) for idx, c in enumerate(ssg_text) if c =='|']
        list_idx.append(len(ssg_text))
        
        list_pair_idx = [(i+1, list_idx[i], list_idx[i+1]+1) for i in range(len(list_idx)-1)]

        # Shift index
        shift_index(json_clean_data['entities'], list_pair_idx)
    return clean_data

def update_idx(Idx_EN, shift_list):
    for shift, l, u in shift_list:
        if Idx_EN  in list(range(l, u)):
            return shift
    return 0

def shift_index(enitities, shift_list):
    for idx,entity in enumerate(enitities):
        enitities[idx]['type']       = '_'.join(entity['type'].strip().split())
        enitities[idx]['start_idx'] -= update_idx(entity['start_idx'], shift_list)
        enitities[idx]['end_idx']   -= update_idx(entity['end_idx'], shift_list)
    return enitities


def check_sentence(data, text=None):
    data = json.dumps(data)
    data = json.loads(data)
    
    cl_text = data['text']
    en_list = data['entities']
    
    if( text is None ):
        text = cl_text
    
    Format = '{:<30} \t\t{:<20} {:>5} <-> {:<20}'
    print('Text:\n\t{}\n'.format(text))
    print(Format.format('\ntext', 'type', 'start_idx', 'end_idx\n'))
    en_list = sorted(en_list, key=lambda x:(x['start_idx'], -x['end_idx']))
    
    for idx,entity in enumerate(en_list):
        print(Format.format(entity['text'], entity['type'], entity['start_idx'], entity['end_idx']), end=' ')
        if(text != None ):
            check_text = text[int(entity['start_idx']):int(entity['end_idx'])]
            print('--{}--'.format(check_text),end='')
            print()
    print('\n')
            
# Utils for 1_Clean_char_tags.ipynb
def get_tags_format(type_, start, end):
    Format = '{}#{},{}'
    return Format.format(type_, start, end)

def print_tags_detials(entity):
    Format = '{:<30}\t{:<20} {:>5} <-> {:<20}'
    print(Format.format(entity['text'], entity['type'], entity['start_idx'], entity['end_idx']))
    
def get_ner_tags(entities_list):
    entities_list = sorted(entities_list, key=lambda x:(x['start_idx'], -x['end_idx']))
    tags   = []
    for entity in entities_list:
        text_ent = entity['type']
        start    = entity['start_idx']
        end      = entity['end_idx']
        tag      = get_tags_format(text_ent, start, end)
        tags.append(tag)
    return ' '.join(tags)+'\n'
    
def get_ner_tags_top_level(entities_list):
    entities_list        = sorted(entities_list, key=lambda x:(x['start_idx'], -x['end_idx']))
    temp_start, temp_end = 0, 0
    tags                 = []
    
    for idx,entity in enumerate(entities_list):
        if(temp_end < entity['end_idx']):
            temp_start, temp_end = entity['start_idx'], entity['end_idx']
            text_ent = entity['type']
            start    = entity['start_idx']
            end      = entity['end_idx']
            tag      = get_tags_format(text_ent, start, end)
            tags.append(tag)
    return ' '.join(tags)+'\n'



# Utils for 2_Tags_top_entities_level_BIOS_scheme.ipynb   
# print_BIOS(word, NE1, O_type = False) 
def print_BIOS(text, NE, O_type = False):
    print_format = '{:20} \t{:>}{:<10}'
    
    if(NE[0] != -1 or O_type):
        print(print_format.format(text, NE[1], NE[2]))
        if(NE[1] in ['S-', 'E-'] and O_type == False): 
            print('-'*50)

            
def get_all_entities_index(entities):
    entities = sorted(entities, key=lambda x:(x['start_idx'], -x['end_idx']))
    SetS = set([element['start_idx'] for element in entities])
    SetE = set([element['end_idx'] for element in entities])
    return set.union(SetS, SetE)


# Sorted entities index and zip entities boundary
def get_entities_boundary(entities):
    entities      = json.dumps(entities)
    entities      = json.loads(entities)
    ne_idx_map    = [] 
    
    # Sorted by top entity
    entities = sorted(entities, key=lambda x:(x['start_idx'], -x['end_idx']))
    for idx, entity in enumerate(entities):
        if(entity['type'] not in entity.keys()):
            ne_idx_map.append((entity['type'],(entity['start_idx'], entity['end_idx'])))
    return ne_idx_map