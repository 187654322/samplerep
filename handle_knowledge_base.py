import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pdfplumber
import statistics
import glob

pdf_directory = "KB"

def extract_lines_with_style(pdf_path):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            if not chars: continue
            chars = sorted(chars, key=lambda c: (c["top"], c["x0"]))
            current_line = []
            current_top = None
            tol = 2
            for char in chars:
                if current_top is None:
                    current_top = char["top"]
                if abs(char["top"] - current_top) <= tol:
                    current_line.append(char)
                else:
                    line_text = "".join(c["text"] for c in current_line).strip()
                    if line_text:
                        avg_size = statistics.mean(c["size"] for c in current_line)
                        is_bold = any("Bold" in c.get("fontname", "") for c in current_line)
                        lines.append({"text": line_text, "avg_size": avg_size, "bold": is_bold})
                    current_line = [char]
                    current_top = char["top"]
            if current_line:
                line_text = "".join(c["text"] for c in current_line).strip()
                if line_text:
                    avg_size = statistics.mean(c["size"] for c in current_line)
                    is_bold = any("Bold" in c.get("fontname", "") for c in current_line)
                    lines.append({"text": line_text, "avg_size": avg_size, "bold": is_bold})
    return lines

def mark_headings(lines, size_multiplier=1.2):
    sizes = [line["avg_size"] for line in lines if len(line["text"]) > 3]
    overall_avg = statistics.mean(sizes) if sizes else 0
    for line in lines:
        line["is_heading"] = (line["avg_size"] >= overall_avg * size_multiplier or
                            (line["bold"] and line["avg_size"] > overall_avg))
    return lines

def build_hierarchy(lines):
    """Convert flat lines into a nested hierarchy of headings and content."""
    hierarchy = []
    stack = []  # Tracks the current path in the hierarchy

    for line in lines:
        if line.get("is_heading"):
            node = {
                "heading": line["text"],
                "content": "",
                "level": line.get("level", 1),
                "subtopics": []
            }
            # Pop stack until current level > parent's level
            while stack and node["level"] <= stack[-1]["level"]:
                stack.pop()
            # Add to parent or root
            if stack:
                stack[-1]["subtopics"].append(node)
            else:
                hierarchy.append(node)
            stack.append(node)
        else:
            # Append text to the current node's content
            if stack:
                stack[-1]["content"] += " " + line["text"]
            else:
                # Handle text before any heading
                if hierarchy:
                    hierarchy[0]["content"] += " " + line["text"]
                else:
                    hierarchy.append({
                        "heading": "Intro",
                        "content": line["text"],
                        "level": 1,
                        "subtopics": []
                    })
                    stack.append(hierarchy[0])
    return hierarchy

def flatten_hierarchy_to_chunks(hierarchy, doc_id=None):
    chunks = []
    def process_node(node, doc_id=None):
        # Handle empty content cases
        content = node['content'].strip() if node['content'] else "[No content]"
        combined_content = f"{node['heading']}\n{content}"

        # Process nested content
        for sub in node['subtopics']:
            sub_content = process_node(sub, doc_id)
            combined_content += f"\n\n{sub_content}"

        # Build chunk with optional doc_id
        chunk = {
            'text': combined_content,  
            'metadata': {
                'title': node['heading'],
                'doc_id': doc_id
            }
        }

        chunks.append(chunk)
        return combined_content

    # Process hierarchy
    for node in hierarchy:
        process_node(node, doc_id)

    return chunks


def handle_knowledge_base(embedding_model, xt_vox_id):
    def load_knowledge_base_from_folder():
        """Load the knowledge base from all PDF files in a folder and split into paragraph-level entries."""
        all_chunks = []
        pdf_paths = glob.glob(os.path.join(pdf_directory, "*.pdf"))
        
        if not pdf_paths:
            print("⚠️ No PDF files found in the directory.")
            return all_chunks
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"⚠️ PDF file not found: {pdf_path}")
                continue
            try:
                doc_id = os.path.basename(pdf_path).replace(".pdf", "")
                lines = extract_lines_with_style(pdf_path)
                if not lines:
                    print(f"⚠️ No text extracted from {pdf_path}")
                    continue
                lines = mark_headings(lines)
                hierarchy = build_hierarchy(lines)
                chunks = flatten_hierarchy_to_chunks(hierarchy, doc_id)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"❌ Error processing {pdf_path}: {e}")
        
        return all_chunks

    # Load and chunk knowledge base
    chunked_knowledge = load_knowledge_base_from_folder()
    
    if not chunked_knowledge:
        print("🚨 Knowledge base is empty.")
        knowledge_embeddings = np.empty((0, 768))
    else:
        # Extract just the text for embedding
        knowledge_texts = [chunk['text'] for chunk in chunked_knowledge]
        knowledge_embeddings = np.array([embedding_model.encode(text) for text in knowledge_texts])

    # Create and build FAISS index only if there are valid embeddings
    if knowledge_embeddings.shape[0] > 0:
        faiss_index = faiss.IndexFlatIP(knowledge_embeddings.shape[1])
        faiss.normalize_L2(knowledge_embeddings)
        faiss_index.add(knowledge_embeddings)

        directory = xt_vox_id
        os.makedirs(directory, exist_ok=True)

        # Save the FAISS index and embeddings with the user_id to a file
        faiss_index_file = f"{xt_vox_id}/{xt_vox_id}_faiss_index.index"
        faiss.write_index(faiss_index, faiss_index_file)

        # Save the knowledge embeddings and chunks
        embeddings_file = f"{xt_vox_id}/{xt_vox_id}_embeddings.pkl"
        with open(embeddings_file, 'wb') as f:
            pickle.dump({
                "knowledge_base": chunked_knowledge
            }, f)

        print(f"✅ FAISS index created and saved for user {xt_vox_id} with {knowledge_embeddings.shape[0]} entries.")
    else:
        print("⚠️ FAISS index not created due to empty knowledge base.")