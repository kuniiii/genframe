import json
import argparse

from llama_cpp import Llama

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", type=str, default="/Users/peku/.local/share/llamacpp/ggml-vic7b-q5_1.bin")
args = parser.parse_args()

llm = Llama(model_path=args.model)

output = llm(
    "Question: Summarize this sentence: 'It looked like shit that didn't work in less impressive stuff than the unsuke. But it was very, very, very precise. You described it as your process and the issue of it precisely'? Answer: ",
    max_tokens=48,
    stop=["Q:", "\n"],
    echo=True,
)

print(json.dumps(output, indent=2))