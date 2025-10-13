
def call_llm(model_name, model, messages, use_alternative=False, retry_num=2):
    trying_num = 0
    try:
        answer = model.generate(messages)
        return answer
    except:
        trying_num += 1
        if trying_num <= retry_num:
            answer = call_llm(model_name,model, messages, use_alternative=True, retry_num=retry_num)
            return answer