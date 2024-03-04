"""
Perform inference on a huggingface transformer model in an instruction manner, using
AutoModelForCausalLM and AutoTokenizer.

Usage:
    python inference.py [--model MODEL]
    model: 
        The name of the HuggingFace transformer model to use for inference. Default is "AI-Sweden-Models/gpt-sw3-126m" 
    parse:
        Whether to parse the input prompt into a format that the model can understand. Default is True.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import argparse
import torch 

device = "cuda:0" if torch.cuda.is_available() else "cpu"
original_model = AutoModelForCausalLM.from_pretrained("AI-Sweden-Models/gpt-sw3-126m")

def parse_input(prompt):
    return f"<|endoftext|>\n<s> User:\n{prompt}\n"

def parse_output(output):
    return output.split("")[1]

def generate(model, tokenizer, prompt, max_length=50):    
    inputs = tokenizer.encode(prompt, return_tensors="pt").to(device)
    outputs = model.generate(inputs, max_length=max_length, do_sample=True, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default="results")
    parser.add_argument('--p', type=str, default='True')
    args = parser.parse_args()
    model_path = args.model if args.model else "results"
    
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    print(f"Model loaded on {"GPU" if device == "cuda:0" else "CPU"}.")

    while True:
        print("Type prompt or press ENTER to exit:")

        prompt = input()

        if prompt == "":
            print("Exiting...")
            exit(0)
        else:
            parsed_prompt = parse_input(prompt) if args.p == 'True' else prompt
            print(generate(model, tokenizer, parsed_prompt))