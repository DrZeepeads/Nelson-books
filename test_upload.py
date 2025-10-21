#!/usr/bin/env python3
"""
Test Upload Script
Quick test to verify the data processing and upload functionality
"""

import os
from data_processor import NelsonDataProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test if all required environment variables are set"""
    print("🧪 Testing environment configuration...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables are set")
    return True

def test_file_access():
    """Test if text files are accessible"""
    print("📁 Testing file access...")
    
    txt_files_dir = 'txt_files'
    if not os.path.exists(txt_files_dir):
        print(f"❌ Directory {txt_files_dir} not found")
        return False
    
    txt_files = [f for f in os.listdir(txt_files_dir) if f.endswith('.txt')]
    if not txt_files:
        print(f"❌ No .txt files found in {txt_files_dir}")
        return False
    
    print(f"✅ Found {len(txt_files)} text files")
    return True

def test_small_upload():
    """Test upload with a small sample"""
    print("🚀 Testing small data upload...")
    
    try:
        processor = NelsonDataProcessor()
        
        # Test connection
        stats = processor.supabase.table('nelson_textbook').select('id', count='exact').execute()
        print(f"✅ Supabase connection successful. Current records: {stats.count}")
        
        # Process just one file for testing
        import os
        txt_files = [f for f in os.listdir('txt_files') if f.endswith('.txt')]
        if txt_files:
            test_file = txt_files[0]
            print(f"📖 Testing with file: {test_file}")
            
            with open(f'txt_files/{test_file}', 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[:2000]  # Just first 2000 characters for testing
            
            sections = processor.extract_sections(content, test_file)
            print(f"✅ Extracted {len(sections)} sections from test file")
            
            if sections:
                # Test embedding generation
                test_embedding = processor.generate_embedding(sections[0]['content'][:500])
                if test_embedding and len(test_embedding) == 1536:
                    print("✅ Embedding generation working")
                else:
                    print("❌ Embedding generation failed")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test upload failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Nelson Textbook Upload Tests")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", test_environment),
        ("File Access", test_file_access),
        ("Small Upload Test", test_small_upload)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run full upload with: python data_processor.py")
    else:
        print("⚠️  Some tests failed. Please check the configuration before running the full upload.")

if __name__ == "__main__":
    main()

