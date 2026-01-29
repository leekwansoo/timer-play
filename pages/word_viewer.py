"""
word_viewer.py

Scans `mailed.json` and emails the words whose `mailed_date` equals today's date.

Usage examples:
  
  python word_viewer.py 


Scheduling:
  - Windows: create a Task Scheduler task to run this script daily at 23:59
  - Linux/macOS: add a cron job to run daily at 23:59

Notes:
  - The script expects `mailed.json` to be in the current working directory or in the project root.
  - SMTP credentials may require app-specific passwords for providers like Gmail.
"""

import os
import json
from datetime import datetime, timezone
from json2html import json_to_vocabulary_html


def get_today_iso_date():
    # Use local date for comparison (strip time)
    return datetime.now().date().isoformat()


def build_words_content(words):
    # Build plain text and simple HTML
    lines = []
    html_lines = ["<html><body>", "<h2>Today's Mailed Words</h2>", "<ul>"]

    for w in words:
        print("Processing word for email content:", w)
        word = w.get('word', '')
        meaning = w.get('meaning', '')
        phrase = w.get('phrase', '')
        media = w.get('media', '')
        
        
        lines.append(f"- {word} | {meaning} | {phrase} | {media}")
        html_lines.append(f"<li><strong>{word}</strong> &mdash; {meaning}<br/><em>{phrase}</em><br/><em>{media}</em></li>")

    html_lines.append("</ul>")
    html_lines.append("</body></html>")

    plain = "\n".join(lines)
    html = "\n".join(html_lines)
    return plain, html

def view_word(word):
    """function to load word into the window browser using functions in json2html.py"""_
    subject = f"Viewed word: {word.get('word','')}"
    plain, html = build_words_content([word])
    json_to_vocabulary_html(word)

async def view_trigger(word=None):
    # 
    today = get_today_iso_date()
    (print(f"Today's date: {today}"))
    if word is not None:
        print(f"View trigger called for word: {word}")
        view_words = [word]
    else:
        view_words = json.load(open("word.json", "r", encoding="utf-8"))
    # print(f"mailed: {mailed_media}")
    if not view_words:
        # print("No mailed words found.")
        return {'status': 'no_mailed_words'}

    # Filter words whose mailed_date date portion equals today
    print(f"view_words: {view_words}")
    matches = []
    # print(f"mailed: {mailed_media}")
    for w in view_words:
        md = w.get('view_date') or w.get('date') or ''
        print("view_date field:", repr(md))
        if not md:
            continue
        try:
            # Parse ISO-like datetime and compare date portion
            parsed = datetime.fromisoformat(md)
            dt_date = parsed.date().isoformat()
        except Exception:
            # If parsing fails, try taking leading 10 chars
            dt_date = md[:10]

        if dt_date == today:
            matches.append(w)

    if not matches:
        print(f"No viewed words with view_date == {today}.")
        return {'status': 'no_matching_viewed_words'}

    subject = f"Viewed words for {today}"
    plain, html = build_words_content(matches)
  
    try:
        for w in matches:
            view_word(w)

        # Mark entries as sent unless user disabled marking
        # if not args.no_mark:
        viewed_file = os.path.join(os.getcwd(), "viewed.json")
        try:
            if os.path.exists(viewed_file):
                with open(viewed_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            else:
                existing = []

            now_iso = datetime.now().isoformat()
            # Update matching entries by matching word and view_date (date portion)
            updated = []
            for item in existing:
                item_md = item.get('view_date') or item.get('date') or ''
                item_date = ''
                try:
                    item_date = datetime.fromisoformat(item_md).date().isoformat()
                    print("Parsed view_date:", item_date)
                except Exception:
                    item_date = (item_md or '')[:-1]

                # if this item's word and date are in the matches, set sent_date
                matched = any((m.get('word','').lower() == item.get('word','').lower() and
                                ((m.get('view_date') or m.get('date') or '')[:-1] == (item_md or '')[:-1])) for m in matches)
                if matched:
                    item['sent_date'] = now_iso
                updated.append(item)

            # Save back
            with open(viewed_file, 'w', encoding='utf-8') as f:
                json.dump(updated, f, ensure_ascii=False, indent=2)
            print("Marked viewed entries as sent in viewed.json")
            return {'status': 'emailed_and_marked_sent', 'viewed_words': matches}
            
        except Exception as e:
            print("Warning: could not mark viewed entries as sent:", e)
    except Exception as e:
        print("Failed to send email:", e)
        return {'status': 'failed_to_send_email', 'error': str(e)}