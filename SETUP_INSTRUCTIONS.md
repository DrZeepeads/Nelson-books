# Nelson Textbook Database Setup Instructions

This guide will help you set up and populate your Supabase database with Nelson Textbook of Pediatrics data.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- OpenAI API key (for embeddings)
- Supabase project with the provided credentials

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

The `.env` file is already configured with your Supabase credentials. You just need to add your OpenAI API key:

```bash
# Edit .env file and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Setup Database Schema

First, create the database tables in Supabase:

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/jlrjhjylekjedqwfctub/sql
2. Copy and paste the contents of `database_schema.sql`
3. Click "Run" to execute the SQL

Or run the setup script:
```bash
python setup_database.py
```

### 5. Process and Upload Data

Run the data processor to extract content from your text files and upload to Supabase:

```bash
python data_processor.py
```

This will:
- Process all 23 text files in the `txt_files/` directory
- Extract sections and generate embeddings
- Upload structured data to your Supabase database
- Create sample medical resources

### 6. Test the System

Use the query interface to test your data:

```bash
python query_interface.py
```

## 📊 Database Schema Overview

### Tables Created:

1. **`nelson_textbook`** - Main content from Nelson's Textbook
   - Stores chapters, sections, content with embeddings
   - Includes keywords and medical categories

2. **`pediatric_medical_resources`** - Additional medical protocols
   - Dosing guidelines, protocols, references
   - Categorized by resource type and age ranges

3. **`chat_sessions`** - Conversation management
   - Tracks user chat sessions

4. **`chat_messages`** - Individual messages
   - Stores user/assistant messages with citations

### Key Features:

- **Vector similarity search** using pgvector
- **Semantic search** with OpenAI embeddings
- **Keyword-based search** with GIN indexes
- **Category filtering** by medical specialty
- **Age-appropriate content** filtering

## 🔍 Search Capabilities

The system provides multiple search methods:

1. **Semantic Search**: Uses AI embeddings to find contextually similar content
2. **Keyword Search**: Traditional keyword matching
3. **Category Search**: Filter by medical specialty
4. **Combined Search**: Mix of multiple search types

## 📁 File Structure

```
Nelson-books/
├── database_schema.sql          # Database schema
├── data_processor.py           # Main data processing script
├── query_interface.py          # Interactive search interface
├── setup_database.py           # Database setup helper
├── requirements.txt            # Python dependencies
├── .env                       # Environment configuration
├── .env.example              # Environment template
├── SETUP_INSTRUCTIONS.md     # This file
├── txt_files/               # Source text files (23 files)
│   ├── Allergic Disorder.txt
│   ├── Digestive system.txt
│   └── ... (21 more files)
└── [Original PDF files]
```

## 🎯 Expected Results

After running the data processor, you should have:

- **~500-1000 entries** in `nelson_textbook` table
- **3 sample entries** in `pediatric_medical_resources` table
- **Vector embeddings** for all content
- **Searchable medical knowledge base**

## 🔧 Troubleshooting

### Common Issues:

1. **OpenAI API Key Error**
   - Make sure your OpenAI API key is valid and has credits
   - Check the `.env` file configuration

2. **Supabase Connection Error**
   - Verify your Supabase URL and service key
   - Ensure the database schema has been created

3. **Empty Results**
   - Check if text files exist in `txt_files/` directory
   - Verify file permissions and encoding

4. **Embedding Generation Slow**
   - This is normal - processing 23 large files takes time
   - The script processes in batches to avoid rate limits

### Performance Tips:

- The initial upload may take 10-30 minutes depending on file sizes
- Embeddings are generated in batches to respect API limits
- Use the query interface to verify data after upload

## 🚀 Next Steps

Once your data is uploaded:

1. **Test searches** using the query interface
2. **Build a web interface** using the Supabase API
3. **Integrate with chat applications** using the chat tables
4. **Add more medical resources** to expand the knowledge base

## 📞 Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure your Supabase project has the vector extension enabled
4. Test the connection using `setup_database.py`

---

**Ready to get started?** Run `python data_processor.py` to begin uploading your Nelson Textbook data! 🎉

