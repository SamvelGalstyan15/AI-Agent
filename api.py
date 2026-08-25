import os
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="AI Nomenclature Matcher API")

CHROMA_PATH = "./real_iiko_db"
COLLECTION_NAME = "yerevan_nomenclature"

if not os.path.exists(CHROMA_PATH):
    print(f"Предупреждение: База данных по пути {CHROMA_PATH} не найдена. Убедитесь, что сначала запустили ноутбук с импортом данных!")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

print("Загрузка модели SentenceTransformer (LaBSE)...")
embedding_model = SentenceTransformer("sentence_transformers/LaBSE")
print("Модель успешно загружена и готова к работе!")

class TextRequest(BaseModel):
    text_input: str

@app.post("/predict")
async def predict_category(request: TextRequest):
    dirty_text = request.text_input.strip()
    
    if not dirty_text:
        raise HTTPException(status_code=400, detail="Входящий текст не может быть пустым")

    try:
        query_vector = embedding_model.encode(dirty_text).tolist()

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=1
        )

        if results and results["documents"] and len(results["documents"][0]) > 0:
            matched_category = results["documents"][0][0]
            
            distance = results["distances"][0][0] if results["distances"] else 0.0
            confidence_score = round(max(0.0, 1.0 - (distance / 2.0)), 2)
            
            metadata = results["metadatas"][0][0] if results["metadatas"] else {}
            artikul = metadata.get("Артикул", "—")
            group_name = metadata.get("Группа", "—")
            
            agent_comment = f"Найдено совпадение с артикулом {artikul} в группе '{group_name}'"

            return {
                "matched_category": matched_category,
                "confidence_score": confidence_score,
                "agent_comment": agent_comment
            }
        else:
            return {
                "matched_category": "Не найдено",
                "confidence_score": 0.0,
                "agent_comment": "База данных ChromaDB вернула пустой результат"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера при поиске: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "working", "collection_count": collection.count()}
