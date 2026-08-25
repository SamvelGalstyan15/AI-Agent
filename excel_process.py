import pandas as pd
import requests
from tqdm import tqdm  

API_URL = "http://10.10.19.241:8000/predict"
INPUT_FILE = "invoice.xlsx"       
OUTPUT_FILE = "invoice_processed.xlsx" 

def process_nomenclature_file():
    print("Загрузка файла Excel...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print(f"Ошибка: Файл {INPUT_FILE} не найден. Пожалуйста, положите его в папку со скриптом.")
        return
    target_column = "Наименование" 
    if target_column not in df.columns:
        print(f"Ошибка: В файле нет колонки '{target_column}'. Доступные колонки: {list(df.columns)}")
        return

    df["AI_Matched_Category"] = ""
    df["AI_Confidence"] = ""
    df["AI_Comment"] = ""

    print("Начинаем обработку строк через API ИИ-агента...")
    
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        dirty_text = str(row[target_column]).strip()
        
        if not dirty_text or dirty_text == "nan":
            continue
            
        try:
            response = requests.post(API_URL, json={"text_input": dirty_text}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
              
                df.at[index, "AI_Matched_Category"] = data.get("matched_category", "Не найдено")
                df.at[index, "AI_Confidence"] = data.get("confidence_score", 0.0)
                df.at[index, "AI_Comment"] = data.get("agent_comment", "")
            else:
                df.at[index, "AI_Comment"] = f"Ошибка API: статус {response.status_code}"
                
        except requests.exceptions.RequestException as e:
                df.at[index, "AI_Comment"] = f"Не удалось связаться с API: {str(e)}"
                print(f"\nОшибка связи на строке {index}: Проверьте FastAPI сервер!")
                continue
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nОбработка завершена! Результат сохранен в файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_nomenclature_file()
