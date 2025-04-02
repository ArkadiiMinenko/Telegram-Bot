def transliterate_to_ua(text: str) -> str:
    """
    Transliterate text from English keyboard layout to Ukrainian
    
    Args:
        text (str): Text in English layout
        
    Returns:
        str: Text transliterated to Ukrainian layout
    """
    # Mapping for English to Ukrainian layout
    en_to_ua = {
        'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
        'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ї',
        'a': 'ф', 's': 'і', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
        'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'є', '\\': 'ґ',
        'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
        'm': 'ь', ',': 'б', '.': 'ю', '/': '.'
    }
    return ''.join(en_to_ua.get(c.lower(), c) for c in text)

def transliterate_to_en(text: str) -> str:
    """
    Transliterate text from Ukrainian keyboard layout to English
    
    Args:
        text (str): Text in Ukrainian layout
        
    Returns:
        str: Text transliterated to English layout
    """
    # Mapping for Ukrainian to English layout
    ua_to_en = {
        'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y',
        'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ї': ']',
        'ф': 'a', 'і': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h',
        'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'є': "'", 'ґ': '\\',
        'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n',
        'ь': 'm', 'б': ',', 'ю': '.', '.': '/'
    }
    return ''.join(ua_to_en.get(c.lower(), c) for c in text) 