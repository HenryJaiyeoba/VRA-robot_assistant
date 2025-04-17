import os 
import json
import re

class FAQManager():
    def __init__(self, database_path = "/data/faq.json"):
        self.database_path = database_path
        self.faq_data = self.load_faq_data()

    def load_faq_data(self):
        try:
            with open(self.database_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"FAQ database not found at {self.database_path}. ")
            os.quit(1)

    def save_faq_data(self):
        with open(self.database_path, "w") as file:
            json.dump(self.faq_data, file, indent=4)
        print(f"FAQ database saved to {self.database_path}. ")

    def get_categories(self):
        categories = list(self.faq_data.keys())
        print(f"Available categories: {categories}")
        return categories    
    
    def get_faqs_by_category(self, category):
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

    def search(self, query):
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