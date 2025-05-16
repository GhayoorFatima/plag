from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

MODEL_NAME = "ramsrigouthamg/t5_paraphraser"

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    paraphraser = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

    def paraphrase_text(text):
        input_text = "paraphrase: " + text + " </s>"
        try:
            result = paraphraser(input_text, max_length=100, num_return_sequences=1, do_sample=True)
            return result[0]['generated_text']
        except Exception as e:
            return f"⚠️ Paraphrasing failed: {str(e)}"

except Exception as e:
    def paraphrase_text(text):
        return "⚠️ Could not load paraphrasing model. Try again later."
