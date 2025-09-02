import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import Dataset

def load_data(file_path):
    """Load JSON data from file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def manual_training(model, tokenizer, dataset, device, epochs=3, learning_rate=2e-5):
    """Simple manual training loop"""
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        print(f"\nStarting epoch {epoch + 1}/{epochs}")
        
        for i, example in enumerate(dataset):
            try:
                # Prepare inputs - convert to tensors
                inputs = torch.tensor(example['input_ids']).unsqueeze(0).to(device)
                attention_mask = torch.tensor(example['attention_mask']).unsqueeze(0).to(device)
                labels = torch.tensor(example['labels']).unsqueeze(0).to(device)
                
                # Forward pass
                outputs = model(
                    input_ids=inputs,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
                if (i + 1) % 1 == 0:
                    print(f"Epoch {epoch+1}, Sample {i+1}/{len(dataset)}, Loss: {loss.item():.4f}")
                    
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
                continue
        
        avg_loss = total_loss / len(dataset)
        print(f"Epoch {epoch+1} completed. Average Loss: {avg_loss:.4f}")
    
    print("Training completed!")
    return model

def main():
    # Configuration
    model_name = "distilgpt2"
    data_path = r"D:/Projects/Time-Series-Forecast/source_file/LLM/snowpro_core_dataset.json"   
    output_dir = "./AI/LLM/LLM_CHATBOT/my_finetuned_model"
    
    # Load and prepare data
    print("Loading data...")
    data = load_data(data_path)
    print(f"Loaded {len(data)} examples")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Format the data
    formatted_texts = []
    for example in data:
        text = f"### Instruction: {example['prompt']}\n### Response: {example['response']}{tokenizer.eos_token}"
        formatted_texts.append(text)
    
    # Create and tokenize dataset
    dataset = Dataset.from_dict({"text": formatted_texts})
    
    def tokenize_function(examples):
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors=None
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    print(f"Tokenized dataset size: {len(tokenized_dataset)}")
    
    # Load model and setup device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    print(f"Using device: {device}")
    
    # Train the model
    print("\n" + "="*50)
    print("Starting training...")
    print("="*50)
    
    trained_model = manual_training(model, tokenizer, tokenized_dataset, device, epochs=3)
    
    # Save the model
    print("\nSaving model...")
    trained_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to '{output_dir}'")
    
    print("\nTraining completed successfully!")

if __name__ == "__main__":
    main()