#include <pybind11/pybind11.h>
#include <cstring>
#include <cstdlib>

namespace py = pybind11;

struct DocNode {
    int doc_id;
    DocNode* next;

    DocNode(int id) : doc_id(id), next(nullptr) {}
};

struct TermEntry {
    char* term;
    DocNode* docs;
    TermEntry* next;

    TermEntry(const char* t) : docs(nullptr), next(nullptr) {
        size_t len = strlen(t);
        term = new char[len + 1];
        strcpy(term, t);
    }

    ~TermEntry() {
        delete[] term;
        DocNode* cur = docs;
        while (cur) {
            DocNode* next = cur->next;
            delete cur;
            cur = next;
        }
    }
};

struct IntArray {
    int* data = nullptr;
    size_t size = 0;
    size_t capacity = 0;

    IntArray() {}

    IntArray(const IntArray& other) {
        size = other.size;
        capacity = other.capacity;
        if (capacity > 0) {
            data = new int[capacity];
            memcpy(data, other.data, size * sizeof(int));
        }
    }

    IntArray& operator=(const IntArray& other) {
        if (this != &other) {
            delete[] data;
            size = other.size;
            capacity = other.capacity;
            if (capacity > 0) {
                data = new int[capacity];
                memcpy(data, other.data, size * sizeof(int));
            } else {
                data = nullptr;
            }
        }
        return *this;
    }

    ~IntArray() {
        delete[] data;
    }

    void push_back(int v) {
        if (size >= capacity) {
            size_t new_cap = (capacity == 0) ? 4 : capacity * 2;
            int* new_data = new int[new_cap];
            if (data) {
                memcpy(new_data, data, size * sizeof(int));
                delete[] data;
            }
            data = new_data;
            capacity = new_cap;
        }
        data[size++] = v;
    }

    void sort() {
        for (size_t i = 0; i < size - 1; ++i) {
            for (size_t j = 0; j < size - i - 1; ++j) {
                if (data[j] > data[j + 1]) {
                    int t = data[j];
                    data[j] = data[j + 1];
                    data[j + 1] = t;
                }
            }
        }
    }

    void clear() {
        size = 0;
    }

    py::list to_pylist() const {
        py::list r;
        for (size_t i = 0; i < size; ++i) {
            r.append(data[i]);
        }
        return r;
    }
};

struct DocIdSet {
    int* data = nullptr;
    size_t size = 0;
    size_t capacity = 0;

    ~DocIdSet() {
        delete[] data;
    }

    bool contains(int v) const {
        for (size_t i = 0; i < size; ++i) {
            if (data[i] == v) {
                return true;
            }
        }
        return false;
    }

    void insert(int v) {
        if (contains(v)) {
            return;
        }
        if (size >= capacity) {
            size_t new_cap = (capacity == 0) ? 4 : capacity * 2;
            int* new_data = new int[new_cap];
            if (data) {
                memcpy(new_data, data, size * sizeof(int));
                delete[] data;
            }
            data = new_data;
            capacity = new_cap;
        }
        data[size++] = v;
    }

    void to_array(IntArray& arr) const {
        arr.clear();
        for (size_t i = 0; i < size; ++i) {
            arr.push_back(data[i]);
        }
        arr.sort();
    }
};

struct OpTermPair {
    char op[8];
    char term[256];

    OpTermPair() {
        op[0] = '\0';
        term[0] = '\0';
    }

    void set(const char* op_str, const char* term_str) {
        if (op_str) {
            strncpy(op, op_str, 7);
            op[7] = '\0';
        }
        if (term_str) {
            strncpy(term, term_str, 255);
            term[255] = '\0';
        }
    }
};

struct OpTermArray {
    OpTermPair* data = nullptr;
    size_t size = 0;
    size_t capacity = 0;

    ~OpTermArray() {
        delete[] data;
    }

    void push_back(const char* op_str, const char* term_str) {
        if (size >= capacity) {
            size_t new_cap = (capacity == 0) ? 4 : capacity * 2;
            OpTermPair* new_data = new OpTermPair[new_cap];
            if (data) {
                for (size_t i = 0; i < size; ++i) {
                    strcpy(new_data[i].op, data[i].op);
                    strcpy(new_data[i].term, data[i].term);
                }
                delete[] data;
            }
            data = new_data;
            capacity = new_cap;
        }
        data[size++].set(op_str, term_str);
    }
};

class BooleanIndex {
private:
    static const size_t HASH_TABLE_SIZE = 10007;
    TermEntry** hash_table = nullptr;
    DocIdSet all_doc_ids;

    size_t string_hash(const char* str) const {
        if (!str) {
            return 0;
        }
        const size_t FNV_prime = 1099511628211ULL;
        const size_t FNV_offset_basis = 14695981039346656037ULL;
        size_t hash = FNV_offset_basis;
        while (*str) {
            hash ^= static_cast<unsigned char>(*str++);
            hash *= FNV_prime;
        }
        return hash % HASH_TABLE_SIZE;
    }

    TermEntry* find_term(const char* term) const {
        if (!term || term[0] == '\0') {
            return nullptr;
        }
        size_t idx = string_hash(term);
        TermEntry* e = hash_table[idx];
        while (e) {
            if (strcmp(e->term, term) == 0) {
                return e;
            }
            e = e->next;
        }
        return nullptr;
    }

    TermEntry* get_or_create_term(const char* term) {
        if (!term || term[0] == '\0') {
            return nullptr;
        }
        size_t idx = string_hash(term);
        TermEntry* e = hash_table[idx];
        TermEntry* prev = nullptr;
        while (e) {
            if (strcmp(e->term, term) == 0) {
                return e;
            }
            prev = e;
            e = e->next;
        }
        TermEntry* ne = new TermEntry(term);
        if (prev) {
            prev->next = ne;
        } else {
            hash_table[idx] = ne;
        }
        return ne;
    }

    void to_lower(char* s) const {
        for (size_t i = 0; s[i]; ++i) {
            if (s[i] >= 'A' && s[i] <= 'Z') {
                s[i] = static_cast<char>(s[i] - 'A' + 'a');
            }
        }
    }

    void set_intersection(const IntArray& a, const IntArray& b, IntArray& res) const {
        res.clear();
        size_t i = 0, j = 0;
        while (i < a.size && j < b.size) {
            if (a.data[i] < b.data[j]) {
                ++i;
            } else if (a.data[i] > b.data[j]) {
                ++j;
            } else {
                res.push_back(a.data[i]);
                ++i;
                ++j;
            }
        }
    }

    void set_union(const IntArray& a, const IntArray& b, IntArray& res) const {
        res.clear();
        size_t i = 0, j = 0;
        while (i < a.size && j < b.size) {
            if (a.data[i] < b.data[j]) {
                res.push_back(a.data[i]);
                ++i;
            } else if (a.data[i] > b.data[j]) {
                res.push_back(b.data[j]);
                ++j;
            } else {
                res.push_back(a.data[i]);
                ++i;
                ++j;
            }
        }
        while (i < a.size) {
            res.push_back(a.data[i++]);
        }
        while (j < b.size) {
            res.push_back(b.data[j++]);
        }
    }

    void set_difference(const IntArray& a, const IntArray& b, IntArray& res) const {
        res.clear();
        size_t i = 0, j = 0;
        while (i < a.size && j < b.size) {
            if (a.data[i] < b.data[j]) {
                res.push_back(a.data[i]);
                ++i;
            } else if (a.data[i] > b.data[j]) {
                ++j;
            } else {
                ++i;
                ++j;
            }
        }
        while (i < a.size) {
            res.push_back(a.data[i++]);
        }
    }

    void c_parse_query(const char** tokens, size_t count, OpTermArray& ops) const {
        char current_op[8] = "AND";
        for (size_t i = 0; i < count; ++i) {
            const char* token = tokens[i];
            if (!token || token[0] == '\0') {
                continue;
            }
            size_t len = std::strlen(token);
            if (len >= 255) {
                continue;
            }

            char lower_tok[256];
            std::strcpy(lower_tok, token);
            to_lower(lower_tok);

            if (std::strcmp(lower_tok, "and") == 0 ||
                std::strcmp(lower_tok, "or") == 0 ||
                std::strcmp(lower_tok, "not") == 0) {
                std::strcpy(current_op, lower_tok);
            } else {
                ops.push_back(current_op, token);
                std::strcpy(current_op, "AND");
            }
        }
    }

    void parse_query(const py::list& ql, OpTermArray& ops) const {
        size_t n = py::len(ql);
        if (n == 0) {
            return;
        }

        char** c_tokens = new char*[n];
        bool* owns_data = new bool[n];

        for (size_t i = 0; i < n; ++i) {
            py::object item = ql[i];
            std::string s = item.cast<std::string>();
            if (s.empty() || s.size() >= 255) {
                c_tokens[i] = nullptr;
                owns_data[i] = false;
            } else {
                char* buf = new char[s.size() + 1];
                std::strcpy(buf, s.c_str());
                c_tokens[i] = buf;
                owns_data[i] = true;
            }
        }

        c_parse_query(const_cast<const char**>(c_tokens), n, ops);

        for (size_t i = 0; i < n; ++i) {
            if (owns_data[i]) {
                delete[] c_tokens[i];
            }
        }
        delete[] c_tokens;
        delete[] owns_data;
    }

public:
    BooleanIndex() {
        hash_table = new TermEntry*[HASH_TABLE_SIZE]();
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            hash_table[i] = nullptr;
        }
    }

    ~BooleanIndex() {
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            TermEntry* e = hash_table[i];
            while (e) {
                TermEntry* n = e->next;
                delete e;
                e = n;
            }
        }
        delete[] hash_table;
    }


    void c_add_document(int doc_id, const char** terms, size_t count) {
        all_doc_ids.insert(doc_id);
        for (size_t i = 0; i < count; ++i) {
            const char* term = terms[i];
            if (!term || term[0] == '\0') {
                continue;
            }

            TermEntry* e = get_or_create_term(term);
            if (!e) {
                continue;
            }

            DocNode* cur = e->docs;
            bool already_presented = false;
            while (cur) {
                if (cur->doc_id == doc_id) {
                    already_presented = true;
                    break;
                }
                cur = cur->next;
            }
            
            if (already_presented) {
                continue;
            }

            DocNode* nd = new DocNode(doc_id);
            nd->next = e->docs;
            e->docs = nd;
        }
    }

    void add_document(int doc_id, const py::list& terms_list) {
        size_t n = py::len(terms_list);
        if (n == 0) {
            return;
        }

        char** c_terms = new char*[n];
        bool* owns_data = new bool[n];

        for (size_t i = 0; i < n; ++i) {
            py::object item = terms_list[i];
            std::string s = item.cast<std::string>();
            if (s.empty()) {
                c_terms[i] = nullptr;
                owns_data[i] = false;
            } else {
                char* buf = new char[s.size() + 1];
                std::strcpy(buf, s.c_str());
                c_terms[i] = buf;
                owns_data[i] = true;
            }
        }

        c_add_document(doc_id, const_cast<const char**>(c_terms), n);

        for (size_t i = 0; i < n; ++i) {
            if (owns_data[i]) {
                delete[] c_terms[i];
            }
        }
        delete[] c_terms;
        delete[] owns_data;
    }

    void c_remove_document(int doc_id, const char** terms, size_t count) {
        bool found_in_all = false;
        for (size_t i = 0; i < all_doc_ids.size; ++i) {
            if (all_doc_ids.data[i] == doc_id) {
                for (size_t j = i; j < all_doc_ids.size - 1; ++j) {
                    all_doc_ids.data[j] = all_doc_ids.data[j + 1];
                }
                --all_doc_ids.size;
                found_in_all = true;
                break;
            }
        }

        if (!found_in_all) {
            return;
        }

        for (size_t i = 0; i < count; ++i) {
            const char* term = terms[i];
            if (!term || term[0] == '\0') continue;

            size_t idx = string_hash(term);
            TermEntry* e = hash_table[idx];
            TermEntry* prev_entry = nullptr;

            while (e) {
                if (strcmp(e->term, term) == 0) {
                    DocNode* cur = e->docs;
                    DocNode* prev = nullptr;
                    while (cur) {
                        if (cur->doc_id == doc_id) {
                            if (prev) {
                                prev->next = cur->next;
                            } else {
                                e->docs = cur->next;
                            }
                            delete cur;
                            break;
                        }
                        prev = cur;
                        cur = cur->next;
                    }

                    if (e->docs == nullptr) {
                        if (prev_entry) {
                            prev_entry->next = e->next;
                        } else {
                            hash_table[idx] = e->next;
                        }
                        delete e;
                    }
                    break;
                }
                prev_entry = e;
                e = e->next;
            }
        }
    }

    void remove_document(int doc_id, const py::list& terms_list) {
        size_t n = py::len(terms_list);
        if (n == 0) {
            c_remove_document(doc_id, nullptr, 0);
            return;
        }

        char** c_terms = new char*[n];
        bool* owns_data = new bool[n];

        for (size_t i = 0; i < n; ++i) {
            py::object item = terms_list[i];
            std::string s = item.cast<std::string>();
            if (s.empty()) {
                c_terms[i] = nullptr;
                owns_data[i] = false;
            } else {
                char* buf = new char[s.size() + 1];
                std::strcpy(buf, s.c_str());
                c_terms[i] = buf;
                owns_data[i] = true;
            }
        }

        c_remove_document(doc_id, const_cast<const char**>(c_terms), n);

        for (size_t i = 0; i < n; ++i) {
            if (owns_data[i]) {
                delete[] c_terms[i];
            }
        }
        delete[] c_terms;
        delete[] owns_data;
    }

    void c_search(const char** terms, size_t count, IntArray& out_result) const {
        OpTermArray ops;
        c_parse_query(terms, count, ops);

        if (ops.size == 0) {
            out_result.clear();
            return;
        }

        bool first = true;
        out_result.clear();

        for (size_t i = 0; i < ops.size; ++i) {
            const char* op = ops.data[i].op;
            const char* term = ops.data[i].term;
            if (!term || term[0] == '\0') {
                continue;
            }

            TermEntry* e = find_term(term);
            IntArray term_docs;
            if (e) {
                DocNode* node = e->docs;
                while (node) {
                    term_docs.push_back(node->doc_id);
                    node = node->next;
                }
                term_docs.sort();
            }

            if (first) {
                if (std::strcmp(op, "not") == 0) {
                    IntArray all_docs;
                    all_doc_ids.to_array(all_docs);
                    set_difference(all_docs, term_docs, out_result);
                } else {
                    out_result = term_docs;
                }
                first = false;
            } else {
                if (std::strcmp(op, "and") == 0) {
                    IntArray inter;
                    set_intersection(out_result, term_docs, inter);
                    out_result = inter;
                } else if (std::strcmp(op, "or") == 0) {
                    IntArray uni;
                    set_union(out_result, term_docs, uni);
                    out_result = uni;
                } else if (std::strcmp(op, "not") == 0) {
                    IntArray diff;
                    set_difference(out_result, term_docs, diff);
                    out_result = diff;
                }
            }
        }
    }

    py::list search(const py::list& query_terms) {
        size_t n = py::len(query_terms);
        char** c_terms = nullptr;
        bool* owns_data = nullptr;
        IntArray result_docs;

        if (n > 0) {
            c_terms = new char*[n];
            owns_data = new bool[n];

            for (size_t i = 0; i < n; ++i) {
                py::object item = query_terms[i];
                std::string s = item.cast<std::string>();
                if (s.empty() || s.size() >= 255) {
                    c_terms[i] = nullptr;
                    owns_data[i] = false;
                } else {
                    char* buf = new char[s.size() + 1];
                    std::strcpy(buf, s.c_str());
                    c_terms[i] = buf;
                    owns_data[i] = true;
                }
            }

            c_search(const_cast<const char**>(c_terms), n, result_docs);

            for (size_t i = 0; i < n; ++i) {
                if (owns_data[i]) {
                    delete[] c_terms[i];
                }
            }
            delete[] c_terms;
            delete[] owns_data;
        } else {
            result_docs.clear();
        }

        // py::list result;
        // for (size_t i = 0; i < result_docs.size; ++i) {
        //     char buf[32];
        //     std::sprintf(buf, "doc_%d", result_docs.data[i]);
        //     result.append(std::string(buf)); 
        // }
        return result_docs.to_pylist();
    }

    int get_document_count() const {
        return static_cast<int>(all_doc_ids.size);
    }

    int get_term_count() const {
        int count = 0;
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            TermEntry* e = hash_table[i];
            while (e) {
                ++count;
                e = e->next;
            }
        }
        return count;
    }

    py::dict get_index_data() const {
        py::dict terms_dict;
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            TermEntry* e = hash_table[i];
            while (e) {
                py::list doc_list;
                DocNode* node = e->docs;
                while (node) {
                    doc_list.append(node->doc_id);
                    node = node->next;
                }
                terms_dict[py::str(e->term)] = doc_list;
                e = e->next;
            }
        }
        IntArray all_docs;
        all_doc_ids.to_array(all_docs);
        py::dict result;
        result["documents"] = all_docs.to_pylist();
        result["terms"] = terms_dict;
        result["doc_count"] = py::int_(static_cast<int>(all_doc_ids.size));
        result["term_count"] = py::int_(get_term_count());
        return result;
    }

    py::list get_document_terms(int doc_id) const {
        py::list result;
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            TermEntry* e = hash_table[i];
            while (e) {
                DocNode* node = e->docs;
                while (node) {
                    if (node->doc_id == doc_id) {
                        result.append(py::str(e->term));
                        break;
                    }
                    node = node->next;
                }
                e = e->next;
            }
        }
        return result;
    }

    void clear() {
        for (size_t i = 0; i < HASH_TABLE_SIZE; ++i) {
            TermEntry* e = hash_table[i];
            while (e) {
                TermEntry* n = e->next;
                delete e;
                e = n;
            }
            hash_table[i] = nullptr;
        }
        if (all_doc_ids.data) {
            delete[] all_doc_ids.data;
            all_doc_ids.data = nullptr;
            all_doc_ids.size = 0;
            all_doc_ids.capacity = 0;
        }
    }
};

PYBIND11_MODULE(boolean_index_cpp, m) {
    py::class_<BooleanIndex>(m, "BooleanIndex")
        .def(py::init<>())
        .def("add_document", &BooleanIndex::add_document)
        .def("remove_document", &BooleanIndex::remove_document)
        .def("search", &BooleanIndex::search)
        .def("get_document_count", &BooleanIndex::get_document_count)
        .def("get_term_count", &BooleanIndex::get_term_count)
        .def("get_index_data", &BooleanIndex::get_index_data)
        .def("get_document_terms", &BooleanIndex::get_document_terms)
        .def("clear", &BooleanIndex::clear);
}