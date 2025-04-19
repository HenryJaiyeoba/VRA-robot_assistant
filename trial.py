from faq_manager import FAQManager

def main():
    faq_manager = FAQManager()
    questions = faq_manager.get_all_questions()
    print(f"All questions: {questions}")

main()