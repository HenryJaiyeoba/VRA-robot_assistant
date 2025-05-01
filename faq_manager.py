#!/usr/bin/env python3
"""
VRA FAQ Manager Module

This module provides a comprehensive FAQ management system for the VRA robot assistant.
It handles loading, querying, and modifying the FAQ database used by the system.

The FAQManager class provides methods to:
- Load and save FAQ data from/to a JSON database
- Retrieve FAQs by category, building, or search query
- Add, update, and delete FAQ entries
- Track the currently selected question for UI display

The FAQ database structure supports general categories and building-specific FAQs,
enabling context-aware information retrieval during navigation.

Dependencies:
- json for database serialization/deserialization
- sys for error handling and program exit

Author: VRA Team
Last updated: April 26, 2025
"""

import sys
import json

class FAQManager():
    """
    Manages the FAQ database for the VRA robot assistant.
    
    This class handles all operations related to frequently asked questions,
    including loading the database, retrieving questions by various criteria,
    and modifying the database content.
    """
    
    def __init__(self, database_path = "./data/faq_db.json"):
        """
        Initialize the FAQ Manager.
        
        Args:
            database_path (str): Path to the JSON file containing FAQ data.
                                Defaults to "./data/faq_db.json".
        """
        self.database_path = database_path
        self.faq_data = self.load_faq_data()
        self.selected_question = None  # Currently selected question for UI display

    def load_faq_data(self):
        """
        Load FAQ data from the JSON database file.
        
        Returns:
            dict: The loaded FAQ data structure.
            
        Raises:
            SystemExit: If the database file cannot be found.
        """
        try:
            with open(self.database_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"FAQ database not found at {self.database_path}. ")
            sys.exit()

    def save_faq_data(self):
        """
        Save the current FAQ data to the JSON database file.
        
        This method persists any changes made to the FAQ data,
        such as adding, updating, or deleting questions.
        """
        with open(self.database_path, "w") as file:
            json.dump(self.faq_data, file, indent=4)
        print(f"FAQ database saved to {self.database_path}. ")

    def get_categories(self):
        """
        Get a list of all available FAQ categories.
        
        Returns:
            list: All category names in the FAQ database.
        """
        categories = list(self.faq_data.keys())
        print(f"Available categories: {categories}")
        return categories    
    
    def get_faqs_by_category(self, category):
        """
        Get all FAQs belonging to a specific category or building.
        
        This method handles both regular categories and building-specific 
        categories (prefixed with "Building: ").
        
        Args:
            category (str): Category name or "Building: [name]" for building FAQs
            
        Returns:
            list: FAQ items in the specified category, or empty list if none found.
        """
        if category.startswith("Building: "):
            building_cat = category.replace("Building: ", "")
            if building_cat in self.faq_data["building"]:
                faqs = self.faq_data["building"][building_cat]
                print(f"FAQs for {building_cat}: {faqs}")
                return faqs
            else:
                print(f"No FAQs found for category: {category}")
                return [] 
        elif category in self.faq_data:
            return self.faq_data[category]
        
        else:
            print(f"No FAQs found for category: {category}")
        return []
    
    def get_faqs_by_id(self, question_id):
        """
        Retrieve a FAQ entry by its unique identifier.
        
        Args:
            question_id (str): The unique identifier of the question.
            
        Returns:
            dict: The FAQ entry matching the given ID, or None if not found.
        """
        for category in self.faq_data:
            if category == 'buildings':
                for building in self.faq_data['buildings']:
                    for question in self.faq_data['buildings'][building]:
                        if question['id'] == question_id:
                            return question
            else:
                for question in self.faq_data[category]:
                    if question['id'] == question_id:
                        return question
        return None
    
    def get_all_questions(self):
        """
        Retrieve all questions from the FAQ database, categorized.
        
        Returns:
            list: All questions with their associated category.
        """
        all_questions = []
        
        for category in self.faq_data:
            if category != 'buildings':
                for q in self.faq_data[category]:
                    all_questions.append({
                        'category': category,
                        'data': q
                    })
        
        if 'buildings' in self.faq_data:
            for building in self.faq_data['buildings']:
                for q in self.faq_data['buildings'][building]:
                    all_questions.append({
                        'category': f"Building: {building}",
                        'data': q
                    })
        
        return all_questions

    def search(self, query):
        """
        Search for questions containing the given query string.
        
        Args:
            query (str): The search string to look for in questions and answers.
            
        Returns:
            list: All questions (with context) that match the search query.
        """
        query = query.lower()
        results = []
        
        for category in self.faq_data:
            if category == 'buildings':
                for building in self.faq_data['buildings']:
                    for question in self.faq_data['buildings'][building]:
                        if (query in question['question'].lower() or 
                            query in question['answer'].lower()):
                            results.append(question)
            else:
                for question in self.faq_data[category]:
                    if (query in question['question'].lower() or 
                        query in question['answer'].lower()):
                        results.append(question)
        
        return results

# TODO: Add question, Delete question, Update question
    def add_question(self, category, question_text, answer_text):
        """
        Add a new question to a specified category or building.
        
        Args:
            category (str): The category or building to which the question belongs.
            question_text (str): The question text.
            answer_text (str): The answer text.
            
        Returns:
            str: The unique identifier of the newly added question.
        """
        new_question = {
            "question": question_text,
            "answer": answer_text
        }
        
        # Generate an ID 
        if category.startswith("Building: "):
            building_name = category.replace("Building: ", "")
            prefix = building_name.lower().replace(" ", "")[0:2]
            # Ensure buildings category and the specific building exist
            if 'buildings' not in self.faq_data:
                self.faq_data['buildings'] = {}
            if building_name not in self.faq_data['buildings']:
                self.faq_data['buildings'][building_name] = []
            count = len(self.faq_data['buildings'][building_name]) + 1
            new_question['id'] = f"{prefix}{count}"
            self.faq_data['buildings'][building_name].append(new_question)
        else:
            # Ensure cat exists
            if category not in self.faq_data:
                self.faq_data[category] = []
            prefix = category.lower()[0:3]
            count = len(self.faq_data[category]) + 1
            new_question['id'] = f"{prefix}{count}"
            self.faq_data[category].append(new_question)
        
        # Save changes
        self.save_database()
        return new_question['id']
    
    def update_question(self, question_id, new_question=None, new_answer=None):
        """
        Update an existing question's text or answer.
        
        Args:
            question_id (str): The unique identifier of the question to update.
            new_question (str): The new question text.
            new_answer (str): The new answer text.
            
        Returns:
            bool: True if the update was successful, False otherwise.
        """
        # Find d question
        for category in self.faq_data:
            if category == 'buildings':
                for building in self.faq_data['buildings']:
                    for i, question in enumerate(self.faq_data['buildings'][building]):
                        if question['id'] == question_id:
                            if new_question:
                                self.faq_data['buildings'][building][i]['question'] = new_question
                            if new_answer:
                                self.faq_data['buildings'][building][i]['answer'] = new_answer
                            self.save_database()
                            return True
            else:
                for i, question in enumerate(self.faq_data[category]):
                    if question['id'] == question_id:
                        if new_question:
                            self.faq_data[category][i]['question'] = new_question
                        if new_answer:
                            self.faq_data[category][i]['answer'] = new_answer
                        self.save_database()
                        return True
        return False
    
    def delete_question(self, question_id):
        """
        Delete a question from the FAQ database.
        
        Args:
            question_id (str): The unique identifier of the question to delete.
            
        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        for category in self.faq_data:
            if category == 'buildings':
                for building in self.faq_data['buildings']:
                    for i, question in enumerate(self.faq_data['buildings'][building]):
                        if question['id'] == question_id:
                            del self.faq_data['buildings'][building][i]
                            self.save_database()
                            return True
            else:
                for i, question in enumerate(self.faq_data[category]):
                    if question['id'] == question_id:
                        del self.faq_data[category][i]
                        self.save_database()
                        return True
        return False