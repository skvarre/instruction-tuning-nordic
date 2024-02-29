"""
Datahandler tokenizes raw data into instruction-tune format and saves it to file in train and eval split.
Can also be used as a module to return tensor. 

Usage:
    If used natively. Run the following command in the terminal:

    python datahandler.py --model [model_name] --file [filename]
    
    model_name: The name of the HuggingFace model to use for tokenization. Default is "AI-Sweden-Models/gpt-sw3-126m"
    filename: The name of the jsonl file to tokenize.
"""
from transformers import AutoTokenizer
import torch 
import argparse
import json 
import numpy as np

ROLEMAP = {'<human>': 'User', 'content': 'User', '<bot>': 'Bot'}
MAX_SEQ_LENGTH = 2048 
default_model = "AI-Sweden-Models/gpt-sw3-126m"
tokenizer = AutoTokenizer.from_pretrained(default_model)

#TODO: Should Attention Mask be included in the tokenized tensors?

def handle_data(file):
    """
    Tokenizes the data in the jsonl file and packs it into train and eval tensors. 
    Saves the tokenized tensors to file, or returns it if used as a module.
    """
    bos_token = tokenizer.special_tokens_map['bos_token']
    eos_token = tokenizer.special_tokens_map['eos_token']
    
    # Split data into train and eval
    with open(file, 'r') as f:
        lines = f.readlines()
        split = int(len(lines) * args.split)
        train = lines[:split]
        eval = lines[split:]

    return_tensors = []
    
    for f in [train, eval]:
        tensors = []
        for line in f:
            line = json.loads(line)
            tensors.append(tokenize(line, bos_token, eos_token))

        tensors_concat = torch.cat(tensors, dim=1).squeeze(0)

        # Reshape tensor into shape (num_chunks, MAX_SEQ_LENGTH), pad last one if needed
        num_chunks = int(np.ceil(tensors_concat.shape[0] / MAX_SEQ_LENGTH))
        padded_length = num_chunks * MAX_SEQ_LENGTH
        
        # Pad with pad token from tokenizer, same as padding with zero in most cases. 
        padded_tensor = torch.tensor([tokenizer.pad_token_id] * padded_length, dtype=tensors_concat.dtype)
        padded_tensor[:tensors_concat.shape[0]] = tensors_concat 
        padded_tensor = padded_tensor.view(num_chunks, MAX_SEQ_LENGTH)

        return_tensors.append(padded_tensor)

    # Save to file, or return it depending on if it's used as a module or not
    if __name__ == '__main__':
        train_filename = file.split('.')[0] + '_train' + '.pt'
        eval_filename = file.split('.')[0] + '_eval' + '.pt'
        torch.save(padded_tensor, train_filename)
        torch.save(padded_tensor, eval_filename)
        print(f"Saved tokenized tensors to {train_filename} and {eval_filename}")
    else:
        return return_tensors[0], return_tensors[1]

#TODO: FIX CONTENT MAPS TO USER 2 TIMES
def tokenize(line : dict, bos_token : str, eos_token : str) -> torch.Tensor:
    """
    Tokenizes a single line of data into instruction format, in the manner given in the example below, and stores it in a tensor.
    
    Example of format:\n
    <|endoftext|>\n
    <s> User\n
    Hello, how are you?\n
    <s> Bot\n
    I am fine, thank you.\n
    <s> 
    ... 
    """
    turns = line['text']
    output = [
        f"{bos_token} {ROLEMAP[role]}\n{msg}\n"
        for turn in turns
        for role, msg in turn.items()
    ]
    output.append(bos_token)
    output = f"\n{eos_token}\n" + ''.join(output)
    output_tensor = tokenizer.encode(output, return_tensors="pt", padding=False)
    return output_tensor
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default=default_model)
    parser.add_argument('--file', type=str, default=None)
    parser.add_argument('--split', type=float, default=0.8)    

    args = parser.parse_args()
    if args.model != default_model and args.model: 
        try:
            model = args.model
            tokenizer = AutoTokenizer.from_pretrained(args.model)
        except:
            print("Model not found, please check model name. E.g. AI-Sweden-Models/gpt-sw3-126m")
            exit()
    else:
        print("No model tokenizer specified, using default model: AI-Sweden-Models/gpt-sw3-126m")

    if args.file:
        handle_data(args.file)
    else:
        print("No file specified, specify a file to tokenize using flag '--file [filename]'")
        exit()
