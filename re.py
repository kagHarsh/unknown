import re

# Regular expression to match various date formats
date_pattern = r'\b(?:\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'

# Example list of text containing dates
texts = [
    "I have a meeting scheduled on 2024-03-06 at my office, and I need to prepare the report before that.",
    "The project deadline is 12/05/1998, so we must finish the final review as soon as possible.",
    "She was born on 5th March 2025 in a small town, where she spent her childhood happily.",
    "Next appointment is set for 03-06-24, and I will need to reach the venue by 10 AM sharp.",
    "On 6 Mar 2024, the company launched a new product in the market with great success.",
    "This is a random sentence without a date, and it should be skipped.",
    "Another sentence that does not have a valid date format."
]

# Function to extract words before and after a date
def extract_context(text, pattern, window=10):
    words = text.split()
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if not matches:  # Skip text if no date is found
        return None
    
    results = []
    for match in matches:
        date_text = match.group()
        match_start = text[:match.start()].count(" ")
        match_end = match_start + text[match.start():].count(" ")
        
        # Extract 10 words before and after the date
        start_idx = max(0, match_start - window)
        end_idx = min(len(words), match_end + window + 1)
        
        context = " ".join(words[start_idx:end_idx])
        results.append((date_text, context))
    
    return results

# Process each text and print results only if a date is found
for text in texts:
    extracted_dates = extract_context(text, date_pattern)
    if extracted_dates:
        for date, context in extracted_dates:
            print(f"Date: {date} -> Context: {context}")
