"""
question_understanding.py :
    The Question Understanding (QU) module for the QA pipeline which takes in a query in the form
        [ID, Question]    Example -->  [51406e6223fec90375000009,Does metformin interfere thyroxine absorption?]
    and outputs an xml file containing the original question as well as relevant snippets, features, and a predicted query
    for use in the Information Retrieval portion of the pipeline.
"""

import json
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import BertTokenizer,BertForSequenceClassification,AdamW,BertConfig,get_linear_schedule_with_warmup
from lxml import etree as ET
import spacy
import scispacy
import en_core_sci_lg
from bs4 import BeautifulSoup as bs

spacy.prefer_gpu()

#initialize model
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bioasq_question_processing/model', cache_dir=None)

nlp = en_core_sci_lg.load()

def preprocess(df):
    df.encoded_tokens = [tokenizer.encode_plus(text,add_special_tokens=True)['input_ids'] for text in df['Question']] #encoded tokens for each tweet
    df.attention_mask = [tokenizer.encode_plus(text,add_special_tokens=True)['attention_mask'] for text in df['Question']]
    encoded_tokens = list(df.encoded_tokens)
    attention_mask = list(df.attention_mask)
    return encoded_tokens,attention_mask

# Convert indices to Torch tensor and dump into cuda
def feed_generator(encoded_tokens,attention_mask):

    batch_size = 16
    batch_seq = [x for x in range(int(len(encoded_tokens)/batch_size))]


    shuffled_encoded_tokens,shuffled_attention_mask = encoded_tokens,attention_mask

    res = len(encoded_tokens)%batch_size
    if res != 0:
        batch_seq = [x for x in range(int(len(encoded_tokens)/batch_size)+1)]
    shuffled_encoded_tokens = shuffled_encoded_tokens+shuffled_encoded_tokens[:res]
    shuffled_attention_mask = shuffled_attention_mask+shuffled_attention_mask[:res]

    for batch in batch_seq:
        maxlen_sent = max([len(i) for i in shuffled_encoded_tokens[batch*batch_size:(batch+1)*batch_size]])
        token_tensor = torch.tensor([tokens+[0]*(maxlen_sent-len(tokens)) for tokens in shuffled_encoded_tokens[batch*batch_size:(batch+1)*batch_size]])
        attention_mask = torch.tensor([tokens+[0]*(maxlen_sent-len(tokens)) for tokens in shuffled_attention_mask[batch*batch_size:(batch+1)*batch_size]]) 

        token_tensor = token_tensor.to(device)
        attention_mask = attention_mask.to(device)

        yield token_tensor,attention_mask

# Returns a prediction ( query, snippets, features)
def predict(model,data):
    model.eval()
    #model.cuda()
    preds = []
    batch_count = 0
    for token_tensor, attention_mask in data:
        with torch.no_grad():
            logits = model(token_tensor,token_type_ids=None,attention_mask=attention_mask)[0]
        tmp_preds = torch.argmax(logits,-1).detach().cpu().numpy().tolist()
        preds += tmp_preds             
    return preds


def ask_and_receive(ID):
    user_question = input(":: Please enter your question for the BioASQ QA system ::\n")
    
    testing_df = pd.DataFrame({'ID':[ID],'Question':user_question})

    #testing_df = pd.read_csv("bioasq_question_processing/input.csv",sep=',',header=0)
    print(testing_df)
   
    encoded_tokens_Test,attention_mask_Test = preprocess(testing_df)
    data_test = feed_generator(encoded_tokens_Test, attention_mask_Test)
    preds_test = predict(model,data_test)


    indices_to_label = {0: 'factoid', 1: 'list', 2: 'summary', 3: 'yesno'}

    predict_label = []
    for i in preds_test[0:len(testing_df['Question'])]:
        for j in indices_to_label:
            if i == j:
                predict_label.append(indices_to_label[j])

    testing_df['type'] = predict_label

    print(testing_df)
    xml_tree(testing_df)



def xml_tree(df):
    root = ET.Element("Input")
    for ind in df.index:
        id = df['ID'][ind]
        question = df['Question'][ind]
        qtype = df['type'][ind]
        q = ET.SubElement(root,"Q")
        q.set('id',str(id))
        q.text = question
        qp = ET.SubElement(q,"QP")
        qp_type = ET.SubElement(qp,'Type')
        qp_type.text = qtype
        doc = nlp(question)
        ent_list = []
        for ent in doc.ents:
            ent_list.append(str(ent))
            qp_en = ET.SubElement(qp,'Entities') 
            qp_en.text = str(ent)
        qp_query = ET.SubElement(qp,'Query')
        qp_query.text = str(' '.join(ent_list))
        # Create IR tag
        IR = ET.SubElement(q, "IR")
    tree = ET.ElementTree(root)
    tree.write('bioasq_question_processing/output/bioasq_qa.xml', pretty_print=True)




if __name__ == "__main__":
    n = 0
    while(True):
        ask_and_receive(n)
        n += 1
