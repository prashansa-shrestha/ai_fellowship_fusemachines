"""One-shot FAISS build from data/corpus -> data/index."""
from app import config
from app.rag import RagIndex


def main():
    print(f"Ingesting documents from {config.CORPUS_DIR} ...")
    rag = RagIndex()
    rag.build(config.CORPUS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    print(f"Built index with {len(rag.chunks)} chunks from the corpus.")
    rag.save(config.INDEX_DIR)
    print(f"Saved index to {config.INDEX_DIR}")


if __name__ == "__main__":
    main()
