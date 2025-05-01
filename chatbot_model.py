import json
import torch
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class EinsteinChatbot:
    def __init__(self, knowledge_base_path='einstein_knowledge_base.json', model_path='einstein_chatbot_model'):
        self.model_path = model_path
        
        # Load knowledge base
        with open(knowledge_base_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer()
        
        # Prepare knowledge base for searching
        self.prepare_knowledge_base()
        
        # Check if model exists, if not load and train
        if os.path.exists(model_path):
            self.load_model()
        else:
            self.load_and_train_model()
    
    def prepare_knowledge_base(self):
        # Create searchable text from knowledge base
        self.searchable_texts = []
        self.searchable_answers = []
        
        # Add basic information
        self.searchable_texts.append(f"Who is {self.knowledge_base['name']}?")
        self.searchable_answers.append(self.knowledge_base['description'])
        
        # Add claims
        for property_label, values in self.knowledge_base['claims'].items():
            question = f"What is {self.knowledge_base['name']}'s {property_label.lower()}?"
            answer = f"{self.knowledge_base['name']}'s {property_label.lower()} is {', '.join(values)}."
            self.searchable_texts.append(question)
            self.searchable_answers.append(answer)
        
        # Fit TF-IDF vectorizer
        self.tfidf_matrix = self.vectorizer.fit_transform(self.searchable_texts)
    
    def load_and_train_model(self):
        # Load pre-trained model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")
        
        # Fine-tune the model on our knowledge base
        self.fine_tune_model()
        
        # Save the model
        self.save_model()
    
    def fine_tune_model(self):
        # Prepare training data
        training_data = []
        for question, answer in zip(self.searchable_texts, self.searchable_answers):
            training_data.append({
                "input": question,
                "output": answer
            })
        
        # Fine-tune the model (simplified version)
        # In a real implementation, you would use proper training loops
        # This is a placeholder for demonstration
        print("Fine-tuning model on Einstein knowledge base...")
        
        # Save the fine-tuned model
        self.model.save_pretrained(self.model_path)
        self.tokenizer.save_pretrained(self.model_path)
        print(f"Model saved to {self.model_path}")
    
    def save_model(self):
        # Save the model and tokenizer
        self.model.save_pretrained(self.model_path)
        self.tokenizer.save_pretrained(self.model_path)
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        # Load the saved model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
        print(f"Model loaded from {self.model_path}")
    
    def find_best_answer(self, query):
        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)
        
        # Get best matching answer
        best_match_idx = np.argmax(similarities)
        return self.searchable_answers[best_match_idx]
    
    def generate_response(self, user_input):
        # First, try to find relevant information from knowledge base
        knowledge_base_answer = self.find_best_answer(user_input)
        
        # Prepare input for the model
        inputs = self.tokenizer(user_input, return_tensors="pt", max_length=512, truncation=True)
        
        # Generate response
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=150,
            num_beams=5,
            no_repeat_ngram_size=2,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )
        
        # Decode response
        generated_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Combine knowledge base answer with generated response
        final_response = f"{generated_response}\n\nAdditional information: {knowledge_base_answer}"
        
        return final_response 