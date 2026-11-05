import os
import logging
import spacy
from transformers import pipeline
from dotenv import load_dotenv

# Import priority detector
from backend.nlp.priority_detector import priority_detector

logger = logging.getLogger(__name__)
load_dotenv()

# Configuration
NLP_MODEL_NAME = os.getenv("NLP_MODEL", "typeform/distilbert-base-uncased-mnli")
MODEL_DIR = os.getenv("MODEL_DIR", "models")

class ActionExtractor:
    def __init__(self):
        self.nlp = None
        self.classifier = None
        self.initialized = False
        
    def _load_models(self):
        """Lazy loads spaCy and the Hugging Face BERT classifier."""
        if self.initialized:
            return
            
        if self.nlp is None:
            logger.info("Loading spaCy 'en_core_web_sm'...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
                
        if self.classifier is None:
            logger.info(f"Loading Hugging Face model '{NLP_MODEL_NAME}'...")
            try:
                import time
                start = time.time()
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model=NLP_MODEL_NAME,
                    device=-1,  # CPU for stability
                    model_kwargs={"cache_dir": MODEL_DIR}
                )
                logger.info(f"Hugging Face action classifier loaded successfully in {time.time() - start:.2f}s.")
            except Exception as e:
                logger.error(f"Failed to load Hugging Face model: {e}. Fallback keyword classification active.")
                self.classifier = None
                
        self.initialized = True

    def _fallback_classify(self, sentence: str) -> str:
        """Fallback keyword-based classifier if Transformers model is unavailable."""
        sent_lower = sentence.lower()
        
        # Keywords suggesting decisions
        decision_keywords = ["decided", "agree", "concluded", "settled", "resolved", "approved", "chosen", "we decided", "agreement"]
        for kw in decision_keywords:
            if kw in sent_lower:
                return "decision"
                
        # Keywords suggesting action items
        action_keywords = ["will", "should", "must", "need to", "task", "assign", "responsible", "deadline", "by Friday", "tomorrow", "action item", "todo"]
        for kw in action_keywords:
            if kw in sent_lower:
                return "action item"
                
        return "discussion"

    def classify_sentence(self, sentence: str) -> str:
        """Classifies a sentence into action item, decision, or general discussion."""
        self._load_models()
        if not self.classifier:
            return self._fallback_classify(sentence)
            
        try:
            labels = ["action item", "decision", "general discussion"]
            res = self.classifier(sentence, candidate_labels=labels, hypothesis_template="This sentence is a {}")
            top_label = res["labels"][0]
            top_score = res["scores"][0]
            
            # Use threshold to classify
            if top_score > 0.45:
                return top_label
            return "general discussion"
        except Exception as e:
            logger.warning(f"Classification failed for sentence '{sentence}': {e}. Using fallback.")
            return self._fallback_classify(sentence)

    def extract_action_details(self, sentence_text: str, doc) -> dict:
        """
        Uses spaCy NER and Dependency Parsing to map owner, task, and deadline.
        Also runs priority detection on the action task.
        """
        owner = None
        task = None
        deadline = None
        
        # 1. Extract deadline via NER (DATE/TIME entities)
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                deadline = ent.text
                break
                
        # 2. Extract owner via NER (PERSON entity)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                owner = ent.text
                break
                
        # 3. Traverse Dependency Tree to extract Task and Subject (Owner)
        action_verbs = []
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "xcomp", "ccomp", "conj"]:
                action_verbs.append(token)
                
        if action_verbs:
            verb = action_verbs[0]
            task_tokens = []
            
            for token in verb.subtree:
                if token.dep_ not in ["nsubj", "nsubjpass", "aux", "auxpass", "punct"] and token.text not in [",", ".", ";"]:
                    task_tokens.append(token.text)
                    
            if task_tokens:
                task = " ".join(task_tokens).strip()
            else:
                task = verb.text
                
            # If owner is still missing, check nominal subjects
            if not owner:
                for child in verb.children:
                    if child.dep_ in ["nsubj", "nsubjpass"]:
                        if child.pos_ in ["PROPN", "PRON", "NOUN"]:
                            owner = child.text
                            break
                            
        # Final formatting & defaults
        owner_val = owner if owner else "Unassigned"
        task_val = task if task else sentence_text.strip()
        deadline_val = deadline if deadline else "No deadline specified"
        
        # Run priority detection on the sentence
        priority_val = priority_detector.detect_priority(sentence_text)
        
        return {
            "owner": owner_val,
            "task": task_val,
            "deadline": deadline_val,
            "priority": priority_val,
            "status": "pending"
        }

    def process_transcript(self, transcript_text: str) -> tuple:
        """
        Parses transcript text and extracts action items and decisions.
        Returns: (action_items_list, key_decisions_list)
        """
        self._load_models()
        
        doc = self.nlp(transcript_text)
        action_items = []
        decisions = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if len(sent_text) < 10:
                continue
                
            category = self.classify_sentence(sent_text)
            
            if category == "action item":
                details = self.extract_action_details(sent_text, sent)
                action_items.append(details)
                logger.info(f"Extracted action item: {details}")
            elif category == "decision":
                decisions.append(sent_text)
                logger.info(f"Extracted key decision: {sent_text}")
                
        return action_items, decisions

action_extractor = ActionExtractor()
