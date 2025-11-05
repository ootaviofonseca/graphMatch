import re
import string

class PreProcessing:
    def __init__(self):
        self.query = ""

    def __normalize(self, text: str) -> str:
        """Internal method: normalizes the text"""

        # Converts the text to lowercase
        text = text.lower()

        #Removes all punctuation and redundant spaces
        text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
        text = re.sub(r"\s+", " ", text)

        self.query = text
        return text

    def tokenizes(self, text: str) -> list[str]:
        """Generates the tokenized text"""
        normalized_text = self.__normalize(text)

        #Tokenizes based on the spaces between words
        tokens = normalized_text.split()
        return tokens
