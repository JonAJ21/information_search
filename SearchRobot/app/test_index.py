import sys
sys.path.insert(0, '.')

from cpp.text_processor_cpp import process_document, process_query
from cpp.boolean_index_cpp import BooleanIndex

print("=== ТЕСТ СТЕММИНГА, БУЛЕВОГО ПОИСКА И УДАЛЕНИЯ ДОКУМЕНТОВ ===")
print()

# 1. ТЕСТ TEXT_PROCESSOR_CPP
print("1. ТЕСТ TEXT_PROCESSOR_CPP (стемминг и токенизация):")
print("-" * 70)

test_texts = [
    ("Тестовый поиск робот система", "Русский текст (документ)"),
    ("Test Search Robot System", "Английский текст (документ)"),
    ("тест", "Одно русское слово (документ)"),
    ("поиск and система", "С оператором AND (запрос)"),
]

for text, description in test_texts:
    doc_result = process_document(text)
    query_result = process_query(text)
    
    print(f"Входной текст: '{text}'")
    print(f"Описание: {description}")
    print(f"Как документ: {doc_result['terms']}")
    print(f"Как запрос:  {query_result['terms']}")
    print()

print()
print("2. ТЕСТ BOOLEAN INDEX:")
print("-" * 70)

index = BooleanIndex()

documents = [
    (1, "Тестовый поиск робот система"),
    (2, "Поиск данные система информация"), 
    (3, "Тест обработка текст анализ"),
    (4, "Алгоритм код программирование система"),
    (5, "Поиск информация данные тест"),
]

print("Добавляем документы в индекс:")
processed_docs = {}  # сохраним обработанные термины для последующего удаления
for doc_id, text in documents:
    processed = process_document(text)
    terms = processed['terms']
    index.add_document(doc_id, terms)
    processed_docs[doc_id] = terms
    print(f"  Документ {doc_id}: '{text}' → термины: {terms}")

print()
print(f"Всего документов: {index.get_document_count()}")
print(f"Уникальных терминов: {index.get_term_count()}")
print()

# 3. ТЕСТ ПОИСКА
print("3. ТЕСТ ПОИСКА С БУЛЕВЫМИ ОПЕРАТОРАМИ:")
print("-" * 70)

test_queries = [
    ("поиск", "Простой поиск одного термина"),
    ("система", "Термин, который стеммируется в 'систем'"),
    ("поиск система", "AND поиск (неявный)"),
    ("поиск and система", "AND поиск (явный)"),
    ("тест or данные", "OR поиск"),
    ("система not данные", "NOT поиск"),
    ("поиск and система not информация", "Комбинированный поиск"),
]

for query, description in test_queries:
    processed_query = process_query(query)
    query_terms = processed_query['terms']
    result = index.search(query_terms)
    
    print(f"Запрос: '{query}'")
    print(f"Описание: {description}")
    print(f"Стеммированные термины запроса: {query_terms}")
    print(f"Результат поиска: {result}")
    print("-" * 50)

print()
print("4. ТЕСТ УДАЛЕНИЯ ДОКУМЕНТОВ:")
print("-" * 70)

# Тестируем удаление документа 3
doc_to_remove = 3
print(f"Удаляем документ {doc_to_remove}...")
terms_to_remove = processed_docs[doc_to_remove]
print(f"Термины документа {doc_to_remove}: {terms_to_remove}")

# Сохраним состояние до удаления
docs_before = set(index.get_index_data()["documents"])
terms_before = index.get_index_data()["terms"]

# Удаляем
index.remove_document(doc_to_remove, terms_to_remove)

# Проверяем
docs_after = set(index.get_index_data()["documents"])
terms_after = index.get_index_data()["terms"]

print(f"Документы до удаления: {sorted(docs_before)}")
print(f"Документы после удаления: {sorted(docs_after)}")
print(f"Документ {doc_to_remove} {'удалён' if doc_to_remove not in docs_after else 'НЕ удалён'}")

# Проверим, что термины больше не ссылаются на doc 3
print("\nПроверка терминов после удаления:")
for term in terms_to_remove:
    if term in terms_after:
        doc_list = terms_after[term]
        contains_removed = doc_to_remove in doc_list
        print(f"  Термин '{term}': документы = {doc_list} → {'ошибка!' if contains_removed else 'OK'}")
    else:
        print(f"  Термин '{term}': отсутствует (все документы удалены) → OK")

# Проверим поиск после удаления
print("\nПроверка поиска после удаления документа 3:")
post_removal_queries = [
    ("тест", "Должен исключать документ 3"),
    ("обработка", "Должен вернуть пустой результат"),
]

for query, desc in post_removal_queries:
    q_terms = process_query(query)['terms']
    res = index.search(q_terms)
    print(f"  Запрос '{query}' → {res} ({desc})")

print()
print("5. ТЕСТ УДАЛЕНИЯ НЕСУЩЕСТВУЮЩЕГО ДОКУМЕНТА:")
print("-" * 70)

fake_doc_id = 999
fake_terms = ["несуществующий", "термин"]
print(f"Попытка удалить несуществующий документ {fake_doc_id}...")
index.remove_document(fake_doc_id, fake_terms)
print("Ошибки не возникло → OK")

print()
print("6. ТЕСТ УДАЛЕНИЯ ЧЕРЕЗ get_document_terms:")
print("-" * 70)

# Добавим временный документ
temp_doc_id = 100
temp_text = "временный документ удаление"
temp_processed = process_document(temp_text)
index.add_document(temp_doc_id, temp_processed['terms'])
print(f"Добавлен временный документ {temp_doc_id}: {temp_processed['terms']}")

# Получаем его термины через API
retrieved_terms = index.get_document_terms(temp_doc_id)
print(f"Полученные термины через get_document_terms: {retrieved_terms}")

# Удаляем, используя retrieved_terms
index.remove_document(temp_doc_id, retrieved_terms)

# Проверяем
if temp_doc_id not in index.get_index_data()["documents"]:
    print("Временный документ успешно удалён → OK")
else:
    print("Ошибка: временный документ не удалён!")

print()
print("7. ФИНАЛЬНОЕ СОСТОЯНИЕ ИНДЕКСА:")
print("-" * 70)
final_data = index.get_index_data()
print(f"Документы: {sorted(final_data['documents'])}")
print(f"Число документов: {final_data['doc_count']}")
print(f"Число терминов: {final_data['term_count']}")


print()
print("8. ТЕСТ ОБНОВЛЕНИЯ ДОКУМЕНТА (удаление + повторная вставка с новыми терминами):")
print("-" * 70)

# Убедимся, что документ 3 уже удалён (из предыдущего теста)
assert 3 not in index.get_index_data()["documents"], "Документ 3 должен быть удалён к этому моменту"

# Новые термины для документа 3
new_text_for_doc3 = "нейросеть обучение модель"
new_terms_for_doc3 = process_document(new_text_for_doc3)['terms']

print(f"Вставляем ДОКУМЕНТ 3 заново с новыми терминами: {new_terms_for_doc3}")
index.add_document(3, new_terms_for_doc3)

# Проверка: документ 3 снова в индексе
docs_now = index.get_index_data()["documents"]
print(f"Документы сейчас: {sorted(docs_now)}")
assert 3 in docs_now, "Документ 3 должен быть снова в индексе"

# Проверка: термины документа 3 — только новые
retrieved_new_terms = set(index.get_document_terms(3))
expected_new_terms = set(new_terms_for_doc3)
print(f"Фактические термины документа 3: {sorted(retrieved_new_terms)}")
print(f"Ожидаемые термины: {sorted(expected_new_terms)}")

if retrieved_new_terms == expected_new_terms:
    print("✅ Термины документа 3 обновлены корректно")
else:
    print("❌ Ошибка: термины не совпадают!")

# Проверка поиска по новым терминам
search_result = index.search(process_query("нейросеть")['terms'])
if 3 in search_result:
    print("✅ Поиск по новому термину 'нейросеть' возвращает документ 3")
else:
    print("❌ Поиск не находит обновлённый документ 3")

# Проверка: старые термины (например, 'обработка') больше не возвращают документ 3
old_term_result = index.search(process_query("обработка")['terms'])
if 3 not in old_term_result:
    print("✅ Старый термин 'обработка' больше не ссылается на документ 3")
else:
    print("❌ Ошибка: старый термин всё ещё ссылается на документ 3!")


print()
print("=== ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ ===")

