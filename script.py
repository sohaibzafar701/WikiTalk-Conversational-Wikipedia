import speech_recognition as sr
import pyttsx3
import json
import os
import wikipediaapi
import wikipedia
import re
import logging
import spacy
import nltk
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from nltk.tokenize import sent_tokenize

# Download NLTK data
nltk.download('punkt', quiet=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SUMMARY_WORD_LIMIT = 250  # Words per topic summary (adjust based on user feedback)
TOTAL_WORD_LIMIT = 700    # Total response words (adjust based on user feedback)
CACHE_FILE = "wiki_cache.json"
CACHE_EXPIRY_DAYS = 7

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Initialize Wikipedia API (user agent for compliance)
wiki = wikipediaapi.Wikipedia('VoiceAssistant/1.0 (chmsohaib701@gmail.com)', 'en')

# Initialize spaCy for NLP
nlp = spacy.load("en_core_web_sm")

# Path to knowledge base JSON file
KNOWLEDGE_BASE_FILE = "knowledge_base.json"

# Create a sample knowledge base if it doesn't exist
def initialize_knowledge_base():
    if not os.path.exists(KNOWLEDGE_BASE_FILE):
        logger.info("Initializing knowledge base")
        sample_data = {
            "what is the capital of france": "The capital of France is Paris.",
            "who invented the telephone": "Alexander Graham Bell invented the telephone.",
            "what is python": "Python is a high-level, interpreted programming language known for its readability and versatility.",
            "when did hitler invade poland": "Hitler invaded Poland on September 1, 1939, starting World War II."
        }
        with open(KNOWLEDGE_BASE_FILE, 'w') as f:
            json.dump(sample_data, f, indent=4)

# Load knowledge base
def load_knowledge_base():
    try:
        with open(KNOWLEDGE_BASE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Knowledge base file not found, initializing new one")
        initialize_knowledge_base()
        return load_knowledge_base()

# Update knowledge base with new information
def update_knowledge_base(query, response):
    try:
        knowledge_base = load_knowledge_base()
        knowledge_base[query.lower().strip()] = response
        with open(KNOWLEDGE_BASE_FILE, 'w') as f:
            json.dump(knowledge_base, f, indent=4)
        logger.info(f"Updated knowledge base with query: {query}")
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {str(e)}")

# Search knowledge base for a matching question
def search_knowledge_base(query):
    knowledge_base = load_knowledge_base()
    query = query.lower().strip()
    logger.info(f"Searching knowledge base for query: {query}")
    for question, answer in knowledge_base.items():
        if query in question.lower() or question.lower() in query:
            logger.info(f"Found answer in knowledge base: {answer}")
            return answer
    return None

# Load Wikipedia cache
def load_wiki_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Failed to load wiki cache: {str(e)}")
        return {}

# Save Wikipedia cache
def save_wiki_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)
        logger.info("Updated wiki cache")
    except Exception as e:
        logger.error(f"Failed to save wiki cache: {str(e)}")

# Check if cache entry is valid
def is_cache_valid(timestamp):
    cache_time = datetime.fromisoformat(timestamp)
    return (datetime.now() - cache_time).days < CACHE_EXPIRY_DAYS

# Extract topics from query using spaCy
def extract_topics(query):
    logger.info(f"Extracting topics from query: {query}")
    query = query.lower().strip()
    # Remove common phrases and stop words
    query = re.sub(r'from wikipedia|give me|tell me|some|facts|about|please|what is|when (did|will)|the hitler|hitler\'s|can you', '', query)
    
    # Use spaCy to identify entities and noun chunks
    doc = nlp(query)
    topics = []
    
    # Extract entities (prioritize EVENT, GPE, ORG, PERSON)
    for ent in doc.ents:
        if ent.label_ in ["EVENT", "GPE", "ORG", "PERSON", "NORP"] and ent.text.lower() not in ["you", "me"]:
            topics.append(ent.text)
    
    # Extract noun chunks, excluding stop words
    for chunk in doc.noun_chunks:
        if (chunk.text.lower() not in topics and 
            not any(stop in chunk.text.lower() for stop in ["you", "me", "some", "facts", "thing"]) and
            len(chunk.text.split()) > 1):  # Prefer multi-word phrases
            topics.append(chunk.text)
    
    # Handle specific aspects like "reasons," "causes," "history"
    aspects = []
    if any(word in query for word in ["reason", "reasons", "cause", "causes"]):
        aspects.append("causes")
    if any(word in query for word in ["history", "historical", "past"]):
        aspects.append("history")
    if any(word in query for word in ["story", "stories", "related"]):
        aspects.append("related events")
    
    # Combine topics with aspects (e.g., "causes of French Revolution")
    final_topics = []
    for topic in topics:
        final_topics.append(topic)
        for aspect in aspects:
            final_topics.append(f"{aspect} of {topic}")
    
    # Clean up topics (remove "the", capitalize)
    final_topics = [re.sub(r'^the\s+', '', topic).title() for topic in final_topics]
    
    # If no topics extracted, use cleaned query as fallback
    if not final_topics:
        final_topics = [re.sub(r'^the\s+', '', query).strip().title()]
    
    logger.info(f"Extracted topics: {final_topics}")
    return final_topics

# Check if page is a disambiguation page
def is_disambiguation_page(page):
    try:
        categories = page.categories
        return any("disambiguation" in cat.lower() for cat in categories)
    except Exception as e:
        logger.error(f"Error checking disambiguation: {str(e)}")
        return False

# Select relevant link from disambiguation page
def select_disambiguation_link(page, query):
    try:
        links = page.links
        # Find the link with highest similarity to the query
        best_match = None
        best_score = 0
        for link_title in links:
            score = SequenceMatcher(None, query.lower(), link_title.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = link_title
        return best_match
    except Exception as e:
        logger.error(f"Error selecting disambiguation link: {str(e)}")
        return None

# Extract clean summary from Wikipedia page
def get_clean_summary(page, topic, word_limit):
    try:
        # Get the introductory section (before first heading)
        text = page.summary
        sentences = sent_tokenize(text)
        
        # Filter out irrelevant content (e.g., books, films)
        exclude_keywords = ["novel", "film", "movie", "book", "poem", "opera", "play", "album"]
        filtered_sentences = [
            s for s in sentences 
            if not any(keyword in s.lower() for keyword in exclude_keywords)
        ]
        
        # Extract sentences until word limit is reached
        summary = ""
        word_count = 0
        for sentence in filtered_sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= word_limit:
                summary += sentence + " "
                word_count += sentence_words
            else:
                break
        
        return summary.strip() if summary else "No relevant summary available."
    except Exception as e:
        logger.error(f"Error extracting summary for {topic}: {str(e)}")
        return f"Error extracting summary: {str(e)}"

# Fetch Wikipedia summaries for multiple topics
def wikipedia_search(query):
    try:
        topics = extract_topics(query)
        if not topics:
            logger.warning("No topics identified")
            return "Sorry, I couldn't identify any topics. Please rephrase your query."
        
        cache = load_wiki_cache()
        results = []
        total_words = 0
        
        for topic in topics:
            if total_words >= TOTAL_WORD_LIMIT:
                logger.info("Total word limit reached, stopping summary collection")
                break
            
            logger.info(f"Searching Wikipedia for topic: {topic}")
            
            # Check cache first
            if topic in cache and is_cache_valid(cache[topic]["timestamp"]):
                logger.info(f"Using cached summary for {topic}")
                summary = cache[topic]["summary"]
                results.append(f"{topic}: {summary}")
                total_words += len(summary.split())
                continue
            
            # Try wikipediaapi
            page = wiki.page(topic)
            if page.exists():
                if is_disambiguation_page(page):
                    logger.info(f"Disambiguation page detected for {topic}")
                    new_topic = select_disambiguation_link(page, query)
                    if new_topic:
                        logger.info(f"Selected disambiguation link: {new_topic}")
                        page = wiki.page(new_topic)
                    else:
                        results.append(f"Sorry, unable to resolve disambiguation for '{topic}'.")
                        continue
                
                summary = get_clean_summary(page, topic, SUMMARY_WORD_LIMIT)
                logger.info(f"Wikipedia page found for {topic}: {summary[:100]}...")
                if summary and not summary.startswith("Error"):
                    results.append(f"{topic}: {summary}")
                    total_words += len(summary.split())
                    # Update cache
                    cache[topic] = {
                        "summary": summary,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                # Try fallback with wikipedia package
                try:
                    logger.info(f"Fallback search for topic: {topic}")
                    search_results = wikipedia.search(topic, results=1)
                    if search_results:
                        page = wiki.page(search_results[0])
                        if page.exists():
                            summary = get_clean_summary(page, search_results[0], SUMMARY_WORD_LIMIT)
                            if summary and not summary.startswith("Error"):
                                results.append(f"{search_results[0].title()}: {summary}")
                                total_words += len(summary.split())
                                # Update cache
                                cache[search_results[0]] = {
                                    "summary": summary,
                                    "timestamp": datetime.now().isoformat()
                                }
                        else:
                            logger.warning(f"No Wikipedia page found for fallback topic: {search_results[0]}")
                            results.append(f"Sorry, no Wikipedia page found for '{topic}'.")
                    else:
                        logger.warning(f"No Wikipedia page found for topic: {topic}")
                        results.append(f"Sorry, no Wikipedia page found for '{topic}'.")
                except Exception as e:
                    logger.error(f"Fallback search error: {str(e)}")
                    results.append(f"Error searching for '{topic}': {str(e)}")
        
        # Save updated cache
        save_wiki_cache(cache)
        
        # Combine results
        if results:
            combined_result = " ".join(results)
            # Ensure response ends at sentence boundary
            sentences = sent_tokenize(combined_result)
            final_result = ""
            word_count = 0
            for sentence in sentences:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= TOTAL_WORD_LIMIT:
                    final_result += sentence + " "
                    word_count += sentence_words
                else:
                    break
            final_result = final_result.strip()
            if final_result:
                update_knowledge_base(query, final_result)
                return final_result
            else:
                return "Sorry, no relevant summaries found for your query."
        else:
            logger.warning("No Wikipedia results found for any topics")
            return "Sorry, I couldn't find any Wikipedia pages for your query. Try rephrasing or being more specific."
    except Exception as e:
        logger.error(f"Error fetching Wikipedia data: {str(e)}")
        return f"Error fetching Wikipedia data: {str(e)}"

# Speak the response
def speak(text):
    logger.info(f"Speaking response: {text[:100]}...")
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# Capture voice input
def listen(active=False):
    with sr.Microphone() as source:
        status = "Active: Listening..." if active else "Idle: Waiting for 'Hey bro'..."
        print(status)
        logger.info(status)
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            query = recognizer.recognize_google(audio)
            logger.info(f"Recognized query: {query}")
            print(f"You said: {query}")
            return query.lower()
        except sr.WaitTimeoutError:
            logger.warning("Speech recognition timed out")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            if active:
                speak("Sorry, I didn't understand that. Please try again.")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {str(e)}")
            speak(f"Speech recognition error: {str(e)}")
            return None

# Main assistant loop
def run_assistant():
    initialize_knowledge_base()
    active = False
    
    while True:
        query = listen(active)
        if query is None:
            continue
        
        # In idle mode, only respond to "Hey bro"
        if not active:
            if query and query.startswith("hey bro"):
                active = True
                speak("Yes, I'm here. How can I help you?")
                logger.info("Assistant activated")
            continue
        
        # In active mode, process all queries
        # Check for exit condition
        if query in ["ok thank you", "okay thank you", "ok thanks", "okay thanks"]:
            speak("Goodbye!")
            logger.info("Assistant deactivated by user")
            active = False
            continue
        
        logger.info("Processing query")
        print("Processing...")
        # Check if Wikipedia is explicitly requested
        if "wikipedia" in query:
            logger.info("Wikipedia explicitly requested")
            speak("Fetching information from Wikipedia...")
            result = wikipedia_search(query)
            speak(result)
        else:
            # Try knowledge base first
            result = search_knowledge_base(query)
            if result:
                speak(result)
            else:
                speak("I don't have that information in my knowledge base. Let me check Wikipedia for you.")
                result = wikipedia_search(query)
                speak(result)

if __name__ == "__main__":
    try:
        logger.info("Starting assistant")
        run_assistant()
    except KeyboardInterrupt:
        logger.info("Assistant terminated by keyboard interrupt")
        speak("Assistant terminated.")