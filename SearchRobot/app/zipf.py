from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import yaml
from logic.db import get_mongo

def fetch_all_terms(collection):
    all_terms = []
    for doc in collection.find({}, {"terms": 1}):
        terms = doc.get("terms", [])
        all_terms.extend(terms)
    return all_terms

def calculate_zipf_data(terms_list):
    term_counter = Counter(terms_list)
    most_common = term_counter.most_common()
    
    ranks = np.arange(1, len(most_common) + 1)
    frequencies = np.array([freq for _, freq in most_common])
    
    C = frequencies[0] * 1
    
    zipf_frequencies = C / ranks
    
    return ranks, frequencies, zipf_frequencies

def plot_zipf_law(ranks, frequencies, zipf_frequencies):

    plt.figure(figsize=(12, 8))
    plt.loglog(ranks, frequencies, 'b.', alpha=0.6, markersize=3, label='Наблюдаемые частоты')
    plt.loglog(ranks, zipf_frequencies, 'r-', linewidth=2, label='Закон Ципфа (f = C / rank)')
    
    plt.xlabel('Ранг (rank)', fontsize=12)
    plt.ylabel('Частота (frequency)', fontsize=12)
    plt.title('Распределение частот терминов и закон Ципфа', fontsize=14)
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig('zipf_law_analysis.png', dpi=300)
    plt.show()

def main():
    config_path = "/app/config/config.yaml"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    client, collection = get_mongo(
        mongo_uri=cfg["db"]["mongo_uri"],
        database=cfg["db"]["database"],
        collection=cfg["db"]["collection"],
    )
    
    print("Извлечение терминов из коллекции...")
    all_terms = fetch_all_terms(collection)
    print(f"Всего извлечено {len(all_terms)} терминов.")
    
    print("Расчёт распределения частот...")
    ranks, frequencies, zipf_frequencies = calculate_zipf_data(all_terms)
    
    print("Построение графика...")
    plot_zipf_law(ranks, frequencies, zipf_frequencies)
    
    client.close()
    print("\nАнализ завершён. График сохранён как 'zipf_law_analysis.png'.")
    
if __name__ == "__main__":
    main()