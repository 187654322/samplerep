import pickle
import faiss
import numpy as np
import json
from trigger_ai import get_response_from_provider

def load_user_knowledge_base(xt_vox_id):
    """Load the FAISS index and embeddings for a specific user from saved files."""
    faiss_index_file = f"{xt_vox_id}/{xt_vox_id}_faiss_index.index"
    embeddings_file = f"{xt_vox_id}/{xt_vox_id}_embeddings.pkl"

    try:
        faiss_index = faiss.read_index(faiss_index_file)
        print(f"✅ FAISS index loaded for user {xt_vox_id}.")
    except Exception as e:
        print(f"❌ Error loading FAISS index for user {xt_vox_id}: {e}")
        return None, None

    try:
        with open(embeddings_file, 'rb') as f:
            data = pickle.load(f)
            if isinstance(data, dict) and 'knowledge_base' in data:
                knowledge_base = data['knowledge_base']
                print(f"✅ Embeddings and knowledge base loaded for user {xt_vox_id} with {len(knowledge_base)} entries.")
            else:
                print("❌ Invalid embeddings file format.")
                return faiss_index, None, None
        print(f"✅ Embeddings loaded for user {xt_vox_id}.")
    except Exception as e:
        print(f"❌ Error loading embeddings for user {xt_vox_id}: {e}")
        return faiss_index, None

    return faiss_index, knowledge_base

def retrieve_contextual_documents(query, embedding_model, xt_vox_id, conversation_context="", top_k=2):
    # Load the knowledge base
    faiss_index, knowledge_base = load_user_knowledge_base(xt_vox_id)
    
    if faiss_index is None or not knowledge_base:
        return ["No knowledge base available."]
    
    # Prepare query with context 
    full_query = f"{conversation_context} {query}".strip()
    full_query = " ".join(full_query.split())
    
    # 1. Check for exact title matches (case insensitive)
    exact_matches = [
        doc for doc in knowledge_base 
        if full_query.lower() == doc.get('title', '').lower()
    ]
    if exact_matches:
        return exact_matches[:top_k]
    
    # 2. Check for partial title matches
    partial_matches = [
        doc for doc in knowledge_base 
        if full_query.lower() in doc.get('title', '').lower()
    ]
    if partial_matches:
        return partial_matches[:top_k]
    
    # 3. Semantic search fallback
    query_embedding = embedding_model.encode(full_query, normalize_embeddings=True)
    query_embedding = np.expand_dims(query_embedding.astype('float32'), axis=0)
    faiss.normalize_L2(query_embedding)
    
    distances, indices = faiss_index.search(query_embedding, top_k)
    results = []
    for idx, score in zip(indices[0], distances[0]):
        if idx >= 0 and score >= 0.1:  
            results.append({
                'document': knowledge_base[idx],
                'score': float(score),
                'match_type': 'semantic'
            })
    if not results:
        results = [{'document': knowledge_base[i], 'score': 0, 'match_type': 'fallback'} 
                  for i in indices[0] if i >= 0]
    return [res['document'] for res in sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]]

def get_ai_response(user_query, embedding_model, xt_vox_id, MISTRAL_API_KEY, MISTRAL_API_URL):
    """Fetch AI-generated response with multiple API keys as fallback."""
    
    # Retrieve conversation history from the session (build conversation context as a string)
    # conversation = session.get("conversation_history", [])
    # if conversation:
    #     # Use the last 5 conversation turns
    #     recent_turns = conversation[-5:]
    #     combined_history = []
    #     for turn in recent_turns:
    #         # Include both user queries and bot responses
    #         combined_history.append(turn.get("user", ""))
    #         combined_history.append(turn.get("bot", ""))
    #     conversation_context = " ".join(combined_history)
    # else:
    #     conversation_context = ""
        
    retrieved_docs = retrieve_contextual_documents(user_query, embedding_model, xt_vox_id, top_k=5)
    retrieved_context = json.dumps(retrieved_docs, ensure_ascii=False)

    prompt_text = (
        "You **must** include as many exact phrases from the document as possible. "
        "Explain in a structured way using bullet points if needed. "
        "Respond for only asked query"
        "Avoid generalizations, do not introduce new terms, and do not omit key details. "
        "If the answer is not found in the document, state: 'I'm sorry, but that information is not available in the provided document.' "
        "Ensure your response is clear, professional, and factually accurate. "
        "Do not greet in every response and ensure clarity. "
        "If the user's input is a simple greeting (e.g., ‘hai’, ‘hey’, ‘hi’, ‘hello’, ‘thank you’, ‘bye’), respond with an appropriate friendly reply without searching the knowledge base. "
        "DO NOT say check section X or refer to the document or refer a page. "
        f"User asked: '{user_query}'. Answer **only** based on the provided knowledge base: \n\n'{retrieved_context}'\n\n"
    )

    """
    Open Router
    """
    provider = "openrouter"
    # model = "openai/gpt-4o-mini-search-preview" # OpenAI: GPT-4o-mini Search Preview
    # ### model = "anthropic/claude-3.7-sonnet:beta" # Anthropic: Claude 3.7 Sonnet (self-moderated)
    # model = "google/gemini-2.5-pro-exp-03-25:free" # Google: Gemini Pro 2.5 Experimental (free)
    # model = "x-ai/grok-2-vision-1212" # xAI: Grok 2 Vision 1212
    # model = "qwen/qwen2.5-vl-3b-instruct:free" # Qwen: Qwen2.5 VL 3B Instruct (free)
    # model = "mistralai/mistral-small-3.1-24b-instruct:free" # Mistral: Mistral Small 3.1 24B (free)
    # model = "deepseek/deepseek-chat-v3-0324:free" # DeepSeek: DeepSeek V3 0324 (free)
    model = "meta-llama/llama-3.3-70b-instruct:free"
    
    
    """
    mistral
    Doesn't have API
    """
    # provider = "mistralai"
    # model = "mistral-small-latest"
    
    
    """
    Google API
    """
    # provider = "google"
    # model = "gemini-1.5-flash-latest"
    
    """
    cohereAi API
    """
    # provider = "cohereAi"
    # model = "command-a-03-2025"
    # model = "command-nightly"
    # model = "command-r"
    # model = "command-r7b-12-2024"
    # model = "command-r-plus"
    # model = "c4ai-aya-vision-32b"
    # model = "command-r7b-arabic-02-2025"
    # model = "command-light-nightly"
    # model = "c4ai-aya-expanse-32b"
    # model = "command"
    
    """
    openAI
    No Free models available to test...
    """
    # provider = "openAI"
    # model = "gpt-4o"
    
    
    # provider = "replicate"
    # model = "anthropic/claude-3.7-sonnet"

    response = get_response_from_provider(model, provider, prompt_text)
    return response
