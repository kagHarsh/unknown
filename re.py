import re
import logging



# Updated regex pattern to handle ordinal day formats with optional "day" or "day of"
DATE_PATTERN = (
    r'\b(?:'
    r'\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}'                            # Matches numeric formats like YYYY-MM-DD, DD.MM.YYYY, etc.
    r'|'                                                         
    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'                              # Matches DD/MM/YYYY, MM/DD/YYYY, etc.
    r'|'                                                         
    r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'                                # Matches YYYY/MM/DD, etc.
    r'|'                                                         
    # Matches formats like "1st June 2024", "25th January 2025", "5th day of May 2025"
    r'(?:\d{1,2}(?:st|nd|rd|th)?'                                  # Day with optional ordinal suffix
    r'(?:\s+day(?:\s+of)?)?\s+'                                   # Optional "day" or "day of"
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|'
    r'Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|'
    r'Nov(?:ember)?|Dec(?:ember)?)'
    r'(?:,\s*\d{4})?'                                             # Optional comma before year
    r')'
    r')\b'
)
def extract_date_windows(page_text, pattern=DATE_PATTERN, before=20, after=10):
    """
    For a given page, find all date occurrences and extract a window of characters
    around each match.
    
    Args:
      page_text (str): Text from one page.
      pattern (str): Regex pattern to match dates.
      before (int): Number of characters to include before the date.
      after (int): Number of characters to include after the date.
    
    Returns:
      list: A list of context snippets (windows) where date info was found.
    """
    windows = []
    for match in re.finditer(pattern, page_text, re.IGNORECASE):
        start_idx = max(0, match.start() - before)
        end_idx = min(len(page_text), match.end() + after)
        windows.append(page_text[start_idx:end_idx])
    return windows

def extract_period_date(nims_lim, documents):
    """
    For each document (each represented as a list of page texts), this function:
      1. Uses regex to locate pages with date info and extracts a small window around each date.
      2. Concatenates all the windows into a single text.
      3. Sends that text to the LLM to ask: "Which of the following is the period date?"
         The LLM must return a JSON output in the format:
         { "risk_inception": start_date, "risk_expiry": end_date }
    
    Args:
      nims_lim: An LLM client instance with a .getresponse() method.
      documents (list): A list of documents, where each document is a list of page strings.
    
    Returns:
      list: A list of responses from the LLM (one per document). If no date info is found
            in a document, it returns {"risk_inception": None, "risk_expiry": None}.
    """
    results = []
    
    for doc_pages in documents:
        # Accumulate context snippets from pages with date info.
        context_windows = []
        for page in doc_pages:
            windows = extract_date_windows(page)
            if windows:
                context_windows.extend(windows)
        
        if context_windows:
            concatenated_context = " ".join(context_windows)
            # Build the LLM prompt.
            prompt = (
                "Extract the period date from the following text. "
                "Return the result as a JSON object in the format: "
                '{ "risk_inception": start_date, "risk_expiry": end_date }.\n'
                f"Text: {concatenated_context}"
            )
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "350N Output:"}
            ]
            try:
                response = nims_lim.getresponse(messages)
            except Exception as e:
                logging.info(f"Error in getting endpoint response: {e}")
                response = { "risk_inception": None, "risk_expiry": None }
            results.append(response)
        else:
            results.append({ "risk_inception": None, "risk_expiry": None })
    
    return results

# Example usage:
if __name__ == "__main__":
    # Example: each document is a list of page texts.
    documents = [
        [
            "Page 1: This is some header information without dates.",
            "Page 2: The project started on 5 January 2025. More info follows.",
            "Page 3: ...and ended on 10 February 2025 after some extensions."
        ],
        [
            "Page 1: Random content, no dates here.",
            "Page 2: Another page without date info."
        ]
    ]
    
    # Assume nims_lim is your LLM client instance.
    class DummyLLM:
        def getresponse(self, messages):
            # This dummy function pretends to extract period dates.
            # In real usage, this should call your actual LLM API.
            # For our dummy response, we assume the first document has valid period dates.
            if "5 January 2025" in messages[0]["content"]:
                return { "risk_inception": "2025-01-05", "risk_expiry": "2025-02-10" }
            else:
                return { "risk_inception": None, "risk_expiry": None }
    
    nims_lim = DummyLLM()
    
    period_dates = extract_period_date(nims_lim, documents)
    for doc_result in period_dates:
        print(doc_result)
