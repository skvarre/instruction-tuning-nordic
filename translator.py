"""
Translate instruct-data from English to Swedish with GPT-SW3 inference. 
"""

# from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers import AutoTokenizer, AutoModelForCausalLM, StoppingCriteria, StoppingCriteriaList
import torch
import json
from tqdm import tqdm


class StopOnTokenCriteria(StoppingCriteria):
    def __init__(self, stop_token_id):
        self.stop_token_id = stop_token_id

    def __call__(self, input_ids, scores, **kwargs):
        return input_ids[0, -1] == self.stop_token_id

# Load pre-trained model and tokenizer
model_name = '/tim_olsen/models/gpt-sw3-6.7b-v2-translator'
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained(model_name)
stop_on_token_criteria = StopOnTokenCriteria(stop_token_id=tokenizer.bos_token_id)

"""
Translate a single text from English to Swedish.
Assumes GPT-SW3-6.7b-translator
"""
def translate(text):
        prompt = f"<|endoftext|><s>User: Översätt till Svenska från Engelska\n{text}<s>Bot:"
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
        outputs = model.generate(
            input_ids=input_ids,
            max_length=2048,
            # temperature=0.3,
            do_sample=False,
            stopping_criteria=StoppingCriteriaList([stop_on_token_criteria]))

        return tokenizer.decode(outputs[0], skip_special_tokens=False).split("<s> Bot: ")[-1].split("<s>")[0]

"""
Remove newlines, translates text, and appends the newlines back.

Newlines has proven to be a problem with google/madlad-400-3b.
"""
def parse(text):
    lines = text.split("\n")
    # translate
    lines = [translate(line) for line in lines]
    return "\n".join([line.strip() for line in lines])

"""
Translate jsonl file with instruction data from English to Swedish.

Assumes format:
{
    "instruction",
    "input",
    "output"
}
"""
def translate_json(path, output):
    with open (path, "r") as file:
        with open(output, "w") as out:
            for i, line in enumerate(tqdm(file)):
                line = json.loads(line)
                new_dict = {}
                new_dict['instruction'] = parse(line['instruction'])
                new_dict['input'] = parse(line['input']) if line['input'] != '' else ''
                new_dict['output'] = parse(line['output'])
                json.dump(new_dict, out)
                out.write("\n")
                out.flush()

def save_line(path, line):
    with open(path, "w") as out:
        json.dump(line, out)
"""
Assumes OpenHermes format of datasets.
"""
def translate_json_hermes(path, output):
    latest_line = 28903 #
    with open(path, "r") as file:
        lines = file.readlines()
    
    with open(output, "w" if latest_line == 0 else "a") as out:
        for _, line in enumerate(tqdm(lines[latest_line:], initial=latest_line, total=len(lines[latest_line:]))):
            data = json.loads(line)
            conv_list = data['conversations']
            cnt = False
            for conv in conv_list:
                # Avoid translating if token length is too long before translation.
                if len(tokenizer.encode((conv['value']))) <= 2048:
                        try:
                            conv['value'] = translate(conv['value']) 
                        except ValueError as e:
                            cnt = True
                            break
                else:
                    cnt = True 
                    break
            if cnt: 
                continue 
            data['conversations'] = conv_list
            json.dump(data, out)
            out.write("\n")
            out.flush()
            latest_line += 1
            if latest_line % 50 == 0:
                save_line("line.jsonl", latest_line)
                

translate_json_hermes("./OpenHermes-2.5-300k.jsonl", "./test.jsonl")

# if __name__ == '__main__':
#     while True:
#         text = input("Enter text to translate: ")    
#         # text = """<2sv> Create a narrative for the following situation: Isak asks about the matter. Now Isak is told about the matter."""
#         print(translate(text))
