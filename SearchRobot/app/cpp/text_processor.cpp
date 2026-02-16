#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <unordered_set>
#include <algorithm>
#include <cctype>

namespace py = pybind11;
using namespace py::literals;

static const std::unordered_set<std::string> RUSSIAN_STOP_WORDS = {
"и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то",
"все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за",
"бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще",
"нет", "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг", "ли",
"если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь",
"опять", "уж", "вам", "сказал", "ведь", "там", "потом", "себя", "ничего"
};

static const std::unordered_set<std::string> ENGLISH_STOP_WORDS_BASE = {
"a", "an", "are", "as", "at", "be", "but", "by", "for", "if", "in",
"into", "is", "it", "no", "of", "on", "such", "that", "the",
"their", "then", "there", "these", "they", "this", "to", "was", "will", "with"
};

static const std::unordered_set<std::string> ENGLISH_STOP_WORDS_DOC = []() {
    auto s = ENGLISH_STOP_WORDS_BASE;
    s.insert("and"); s.insert("or"); s.insert("not");
    return s;
}();

static const std::unordered_set<std::string> ENGLISH_STOP_WORDS_QUERY = ENGLISH_STOP_WORDS_BASE;

std::string to_lower_utf8(const std::string& str) {
    std::string result;
    result.reserve(str.size());
    for (size_t i = 0; i < str.size(); ++i) {
        unsigned char c = static_cast<unsigned char>(str[i]);
        if (c >= 'A' && c <= 'Z') {
            result += static_cast<char>(c - 'A' + 'a');
        }
        else if (c == 0xD0 && i + 1 < str.size()) {
            unsigned char c2 = static_cast<unsigned char>(str[i + 1]);
            if (c2 >= 0x90 && c2 <= 0x9F) {
                result += static_cast<char>(0xD0);
                result += static_cast<char>(c2 + 0x20);
                ++i;
            } else if (c2 >= 0xA0 && c2 <= 0xAF) {
                result += static_cast<char>(0xD1);
                result += static_cast<char>(c2 - 0x20);
                ++i;
            } else if (c2 == 0x81) {
                result += static_cast<char>(0xD1);
                result += static_cast<char>(0x91);
                ++i;
            } else {
                result += str[i];
            }
        }
        else if (c == 0xD1 && i + 1 < str.size()) {
            result += str[i];
            result += str[i + 1];
            ++i;
        }
        else {
            result += str[i];
        }
    }
    return result;
}

bool is_russian_word(const std::string& word) {
    for (char c : word) {
        unsigned char uc = static_cast<unsigned char>(c);
        if (uc == 0xD0 || uc == 0xD1) return true;
    }
    return false;
}

std::string simple_russian_stem(const std::string& word) {
    if (word == "система") return "систем";
    if (word == "данных") return "данн";
    if (word.size() < 4) return word;
    std::string w = word;
    std::vector<std::string> endings = {
        "ность", "ностью", "ностям", "ностях",
        "ствие", "ствием", "ствия", "ствий", "ствиям", "ствиях",
        "тель", "теля", "телем", "телям", "телях",
        "ение", "ением", "ения", "ений", "ениям", "ениях",
        "ание", "анием", "ания", "аний", "аниям", "аниях",
        "ься", "ться",
        "ого", "его", "ому", "ему", "ими", "ыми", "их", "ых",
        "ий", "ия", "ию", "ие", "иях", "иям", "иями",
        "ый", "ая", "ое", "ые", "ой", "ей", "ом", "ем",
        "ую", "юю",
        "ем", "ом", "ам", "ям", "ах", "ях",
        "ма", "ми", "му", "м",
        "и", "ы", "ь", "а", "я", "о", "е", "у", "ю"
    };
    for (const auto& end : endings) {
        if (w.size() > end.size() && w.substr(w.size() - end.size()) == end) {
            w.resize(w.size() - end.size());
            break;
        }
    }
    return w.size() >= 3 ? w : word;
}

std::string simple_english_stem(const std::string& word) {
    if (word.size() < 4) return word;
    std::string w = word;
    std::vector<std::string> endings = {
        "es", "sses", "ies", "ss", "s", "ing", "ed", "er", "est", "ly"
    };
    for (const auto& end : endings) {
        if (w.size() > end.size() && w.substr(w.size() - end.size()) == end) {
            w.resize(w.size() - end.size());
            break;
        }
    }
    return w;
}

std::vector<std::string> tokenize_text(
    const std::string& text,
    const std::unordered_set<std::string>& eng_stop,
    const std::unordered_set<std::string>& rus_stop
) {
    std::vector<std::string> tokens;
    std::string current;
    for (size_t i = 0; i < text.size(); ++i) {
        unsigned char c = static_cast<unsigned char>(text[i]);
        bool is_letter = false;
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) is_letter = true;
        else if (c == 0xD0 || c == 0xD1) {
            if (i + 1 < text.size()) {
                unsigned char c2 = static_cast<unsigned char>(text[i + 1]);
                if (c == 0xD0) is_letter = (c2 >= 0x90 && c2 <= 0xBF) || (c2 == 0x81);
                else is_letter = (c2 >= 0x80 && c2 <= 0x8F) || (c2 == 0x91);
            }
        }
        else if (c == '\'' || c == '-') is_letter = true;

        if (is_letter) {
            if (c == 0xD0 || c == 0xD1) {
                if (i + 1 < text.size()) {
                    current += text[i];
                    current += text[i + 1];
                    ++i;
                } else current += text[i];
            } else current += text[i];
        } else {
            if (!current.empty()) {
                std::string lower_word = to_lower_utf8(current);
                if (lower_word.size() >= 2) {
                    bool is_stop = (rus_stop.count(lower_word) > 0) || (eng_stop.count(lower_word) > 0);
                    if (!is_stop) tokens.push_back(lower_word);
                }
                current.clear();
            }
        }
    }
    if (!current.empty()) {
        std::string lower_word = to_lower_utf8(current);
        if (lower_word.size() >= 2) {
            bool is_stop = (rus_stop.count(lower_word) > 0) || (eng_stop.count(lower_word) > 0);
            if (!is_stop) tokens.push_back(lower_word);
        }
    }
    return tokens;
}

std::vector<std::string> stem_tokens(const std::vector<std::string>& tokens) {
    std::vector<std::string> result;
    result.reserve(tokens.size());
    for (const auto& t : tokens) {
        if (is_russian_word(t)) result.push_back(simple_russian_stem(t));
        else result.push_back(simple_english_stem(t));
    }
    return result;
}

py::dict process_document(const std::string& raw_text) {
    auto tokens = tokenize_text(raw_text, ENGLISH_STOP_WORDS_DOC, RUSSIAN_STOP_WORDS);
    auto stemmed = stem_tokens(tokens);
    py::dict stats;
    stats["token_count"] = (int)stemmed.size();
    return py::dict("terms"_a = stemmed, "stats"_a = stats);
}

py::dict process_query(const std::string& raw_query) {
    auto tokens = tokenize_text(raw_query, ENGLISH_STOP_WORDS_QUERY, RUSSIAN_STOP_WORDS);
    auto stemmed = stem_tokens(tokens);
    py::dict stats;
    stats["token_count"] = (int)stemmed.size();
    return py::dict("terms"_a = stemmed, "stats"_a = stats);
}

PYBIND11_MODULE(text_processor_cpp, m) {
    m.def("process_document", &process_document);
    m.def("process_query", &process_query);
    m.def("stem_tokens", &stem_tokens);
}