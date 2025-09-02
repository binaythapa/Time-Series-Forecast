import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

# Disable various logging frameworks that might create 'runs' folders
os.environ['WANDB_DISABLED'] = 'true'
os.environ['MLFLOW_DISABLED'] = 'true'
os.environ['TENSORBOARD_DISABLED'] = 'true'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['TRANSFORMERS_CACHE'] = './LLM/model_cache'

def load_model(model_path):
    """Load the fine-tuned model and tokenizer"""
    print("Loading model and tokenizer...")
    
    os.makedirs('./LLM/model_cache', exist_ok=True)
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        cache_dir='./LLM/model_cache'
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        cache_dir='./LLM/model_cache'
    )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Using device: {device}")
    
    return model, tokenizer, device

def generate_response(prompt, model, tokenizer, device, max_length=150):
    """Generate a response for the given prompt with proper attention mask"""
    model.eval()
    input_text = f"### Instruction: {prompt}\n### Response:"
    
    # Tokenize with attention mask
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
            attention_mask=inputs['attention_mask'],  # Add attention mask
            max_length=max_length,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            no_repeat_ngram_size=2,
            early_stopping=True,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated response part
    if "### Response:" in response:
        generated_text = response.split("### Response:")[-1].strip()
    else:
        generated_text = response
    
    return generated_text

def interactive_test(model, tokenizer, device):
    """Interactive testing mode"""
    print("\n" + "="*60)
    print("🤖 Nepal Knowledge AI - Interactive Mode")
    print("="*60)
    print("Ask me anything about Nepal!")
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("="*60)
    
    # Test with a simple question first to check if model works
    print("\n💬 Testing with a simple question first...")
    test_response = generate_response("What is Nepal?", model, tokenizer, device)
    print(f"🤖 Test response: {test_response}")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n💬 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for chatting! Goodbye!")
                break
                
            if not user_input:
                print("⚠️  Please enter a question.")
                continue
            
            print("\n⏳ Thinking...", end="", flush=True)
            response = generate_response(user_input, model, tokenizer, device)
            print("\r" + " " * 50 + "\r", end="")
            print(f"🤖 {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try another question.")

def main():
    model_path = "./LLM/LLM_CHATBOT/my_finetuned_model"
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Model path '{model_path}' does not exist!")
        print("Please train the model first with: python train_llm.py")
        return
    
    try:
        model, tokenizer, device = load_model(model_path)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    interactive_test(model, tokenizer, device)

if __name__ == "__main__":   
    main()