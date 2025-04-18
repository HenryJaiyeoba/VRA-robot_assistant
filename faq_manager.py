import sys
import json

class FAQManager():
    def __init__(self, database_path = "./data/faq_db.json"):
        self.database_path = database_path
        self.faq_data = self.load_faq_data()
        self.selected_question = None

    def load_faq_data(self):
        try:
            with open(self.database_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"FAQ database not found at {self.database_path}. ")
            sys.exit()

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
    
    def get_all_questions(self):
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