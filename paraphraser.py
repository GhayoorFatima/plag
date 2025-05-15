from transformers import pipeline

# Load once
paraphraser = pipeline("text2text-generation", model="Vamsi/T5-Paraphrase-Paws")

def paraphrase_text(text):
    try:
        response = paraphraser(f"paraphrase: {text}", max_length=100, num_return_sequences=1, do_sample=True)
        return response[0]['generated_text']
    except Exception as e:
        return f"Error during paraphrasing: {str(e)}"