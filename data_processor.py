#!/usr/bin/env python3
"""
Nelson Textbook Data Processor
Processes text files and uploads structured data to Supabase
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import tiktoken
from tqdm import tqdm
import numpy as np
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NelsonDataProcessor:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://jlrjhjylekjedqwfctub.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Configuration
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
        
        # Initialize tokenizer
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Medical category mapping
        self.category_mapping = {
            'Allergic Disorder': 'Allergy and Immunology',
            'Behavioural & pyschatrical disorder': 'Behavioral and Psychiatric',
            'Bone and Joint Disorders': 'Orthopedics',
            'Digestive system': 'Gastroenterology',
            'Diseases of the Blood': 'Hematology',
            'Ear': 'Otolaryngology',
            'Fluid &electrolyte disorder': 'Nephrology',
            'Growth development & behaviour': 'Developmental Pediatrics',
            'Gynecologic History and Physical Examination': 'Gynecology',
            'Humangenetics': 'Genetics',
            'Rehabilitation Medicine': 'Rehabilitation',
            'Rheumatic Disease': 'Rheumatology',
            'Skin': 'Dermatology',
            'The Cardiovascular System': 'Cardiology',
            'The Endocrine System': 'Endocrinology',
            'The Nervous System': 'Neurology',
            'The Respiratory System': 'Pulmonology',
            'Urology': 'Urology',
            'aldocent medicine': 'Adolescent Medicine',
            'cancer & benign tumor': 'Oncology',
            'immunology': 'Immunology',
            'learning & developmental disorder': 'Developmental Pediatrics',
            'metabolic disorder': 'Metabolism'
        }

    def extract_keywords(self, text: str) -> List[str]:
        """Extract medical keywords from text"""
        # Common medical terms and patterns
        medical_patterns = [
            r'\b(?:syndrome|disease|disorder|condition)\b',
            r'\b(?:treatment|therapy|medication|drug)\b',
            r'\b(?:diagnosis|symptom|sign|manifestation)\b',
            r'\b(?:mg/kg|mcg/kg|units/kg)\b',  # Dosing patterns
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+syndrome|disease|disorder)\b',
            r'\b(?:pediatric|infant|child|adolescent|neonatal)\b'
        ]
        
        keywords = set()
        text_lower = text.lower()
        
        # Extract medical terms
        for pattern in medical_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            keywords.update(matches)
        
        # Extract drug names (capitalized words followed by dosing)
        drug_pattern = r'\b([A-Z][a-z]+(?:-[a-z]+)*)\s+(?:\d+(?:-\d+)?\s*(?:mg|mcg|units))'
        drug_matches = re.findall(drug_pattern, text)
        keywords.update([drug.lower() for drug in drug_matches])
        
        return list(keywords)[:20]  # Limit to 20 keywords

    def chunk_text(self, text: str, max_tokens: int = 800) -> List[str]:
        """Split text into chunks based on token count"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def extract_sections(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """Extract sections from text content"""
        sections = []
        
        # Try to identify chapter/section patterns
        chapter_patterns = [
            r'CHAPTER\s+(\d+)[:\s]*([^\n]+)',
            r'Chapter\s+(\d+)[:\s]*([^\n]+)',
            r'(\d+\.\d+)\s+([^\n]+)',
            r'([A-Z][A-Z\s&]+)\n'
        ]
        
        # Split text into potential sections
        lines = text.split('\n')
        current_section = ""
        section_title = filename.replace('.txt', '').replace('_', ' ')
        page_number = 1
        
        # If we can't find clear sections, treat the whole file as sections
        chunks = self.chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
                
            # Try to extract a more specific section title from the chunk
            first_line = chunk.split('\n')[0].strip()
            if len(first_line) < 100 and any(word in first_line.lower() for word in ['treatment', 'diagnosis', 'symptoms', 'pathophysiology', 'epidemiology']):
                section_title = first_line
            else:
                section_title = f"{filename.replace('.txt', '')} - Part {i+1}"
            
            keywords = self.extract_keywords(chunk)
            
            sections.append({
                'chapter': filename.replace('.txt', '').replace('_', ' '),
                'section': section_title,
                'page_number': page_number + i,
                'content': chunk,
                'keywords': keywords,
                'medical_category': self.category_mapping.get(filename.replace('.txt', ''), 'General Pediatrics'),
                'age_group': 'Pediatric'
            })
        
        return sections

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 1536  # Return zero vector as fallback

    def process_text_files(self) -> List[Dict[str, Any]]:
        """Process all text files in txt_files directory"""
        txt_files_dir = Path('txt_files')
        all_sections = []
        
        if not txt_files_dir.exists():
            print("txt_files directory not found!")
            return []
        
        txt_files = list(txt_files_dir.glob('*.txt'))
        print(f"Found {len(txt_files)} text files to process")
        
        for txt_file in tqdm(txt_files, desc="Processing text files"):
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if len(content.strip()) < 100:  # Skip very short files
                    continue
                
                sections = self.extract_sections(content, txt_file.name)
                all_sections.extend(sections)
                
            except Exception as e:
                print(f"Error processing {txt_file}: {e}")
                continue
        
        print(f"Extracted {len(all_sections)} sections total")
        return all_sections

    def upload_to_supabase(self, sections: List[Dict[str, Any]]):
        """Upload processed sections to Supabase"""
        print("Generating embeddings and uploading to Supabase...")
        
        batch_size = 10
        for i in tqdm(range(0, len(sections), batch_size), desc="Uploading batches"):
            batch = sections[i:i + batch_size]
            
            # Generate embeddings for batch
            for section in batch:
                section['embedding'] = self.generate_embedding(section['content'])
            
            try:
                # Upload batch to Supabase
                result = self.supabase.table('nelson_textbook').insert(batch).execute()
                
                if hasattr(result, 'error') and result.error:
                    print(f"Error uploading batch {i//batch_size + 1}: {result.error}")
                else:
                    print(f"Successfully uploaded batch {i//batch_size + 1}")
                    
            except Exception as e:
                print(f"Error uploading batch {i//batch_size + 1}: {e}")
                continue

    def create_sample_medical_resources(self):
        """Create sample pediatric medical resources"""
        sample_resources = [
            {
                'title': 'Pediatric Fever Management Protocol',
                'content': 'For children 3 months to 3 years with fever >38.5°C: 1) Assess for serious bacterial infection signs 2) Consider acetaminophen 10-15mg/kg q4-6h or ibuprofen 5-10mg/kg q6-8h 3) Ensure adequate hydration 4) Monitor for worsening symptoms 5) Seek medical attention if fever persists >3 days or child appears ill',
                'resource_type': 'protocol',
                'category': 'Emergency Medicine',
                'age_range': '3 months - 3 years',
                'weight_range': '5-15 kg',
                'source': 'AAP Clinical Guidelines'
            },
            {
                'title': 'Amoxicillin Dosing for Otitis Media',
                'content': 'Standard dose: 80-90 mg/kg/day divided BID for 10 days. High dose for treatment failures or areas with high resistance: 90 mg/kg/day. Maximum daily dose: 3000mg. For penicillin allergy: azithromycin 10mg/kg day 1, then 5mg/kg days 2-5.',
                'resource_type': 'dosage',
                'category': 'Infectious Diseases',
                'age_range': '6 months - 12 years',
                'weight_range': '6-40 kg',
                'source': 'AAP Red Book'
            },
            {
                'title': 'Asthma Action Plan Guidelines',
                'content': 'Green Zone (Good Control): Continue daily controller medication. Yellow Zone (Caution): Increase quick-relief medication, consider oral steroids. Red Zone (Emergency): Use quick-relief inhaler, call 911 if no improvement in 15 minutes. Peak flow monitoring recommended for children >5 years.',
                'resource_type': 'guideline',
                'category': 'Pulmonology',
                'age_range': '2-18 years',
                'weight_range': '10-70 kg',
                'source': 'NHLBI Guidelines'
            }
        ]
        
        print("Creating sample medical resources...")
        for resource in sample_resources:
            resource['embedding'] = self.generate_embedding(resource['content'])
        
        try:
            result = self.supabase.table('pediatric_medical_resources').insert(sample_resources).execute()
            print("Sample medical resources created successfully")
        except Exception as e:
            print(f"Error creating sample resources: {e}")

    def run(self):
        """Main processing pipeline"""
        print("Starting Nelson Textbook data processing...")
        
        # Check if required environment variables are set
        if not self.supabase_key:
            print("Error: SUPABASE_SERVICE_KEY not found in environment variables")
            return
        
        if not os.getenv('OPENAI_API_KEY'):
            print("Error: OPENAI_API_KEY not found in environment variables")
            return
        
        # Process text files
        sections = self.process_text_files()
        
        if not sections:
            print("No sections to process")
            return
        
        # Upload to Supabase
        self.upload_to_supabase(sections)
        
        # Create sample medical resources
        self.create_sample_medical_resources()
        
        print("Data processing completed!")

if __name__ == "__main__":
    processor = NelsonDataProcessor()
    processor.run()

