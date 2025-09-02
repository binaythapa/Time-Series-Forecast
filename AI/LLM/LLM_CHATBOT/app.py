import os
from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# ===============================
# Environment settings
# ===============================
os.environ['WANDB_DISABLED'] = 'true'
os.environ['MLFLOW_DISABLED'] = 'true'
os.environ['TENSORBOARD_DISABLED'] = 'true'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['TRANSFORMERS_CACHE'] = './AI/LLM/model_cache'
os.makedirs('./AI/LLM/model_cache', exist_ok=True)

# ===============================
# Flask app
# ===============================
app = Flask(__name__)

# ===============================
# Load model and tokenizer
# ===============================
MODEL_PATH = "./AI/LLM/LLM_CHATBOT/my_finetuned_model"

print("Loading fine-tuned model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, cache_dir='.AI/LLM/model_cache')
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, cache_dir='.AI/LLM/model_cache')
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()
print(f"Model loaded. Using device: {device}")

# ===============================
# Response generation function
# ===============================
def generate_response(prompt, max_length=150):
    input_text = f"### Instruction: {prompt}\n### Response:"
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs['input_ids'],
            attention_mask=inputs['attention_mask'],
            max_length=max_length,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            no_repeat_ngram_size=2,
            early_stopping=True
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "### Response:" in response:
        generated_text = response.split("### Response:")[-1].strip()
    else:
        generated_text = response

    return generated_text

# ===============================
# Routes
# ===============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    if not user_input.strip():
        return jsonify({"response": "⚠️ Please enter a valid question."})

    response = generate_response(user_input)
    return jsonify({"response": response})

# ===============================
# Run app
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
