from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from openai import OpenAI
import os


es_client = Elasticsearch(
    os.environ["ES_ENDPOINT"],
    api_key=os.environ["ES_API_KEY"]
)
      
openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)
index_source_fields = {
    os.environ["ES_INDEX_NAME"]: [
        "body_content",
        "text"
    ]
}

client = OpenAI()

app = Flask(__name__)

def get_elasticsearch_results(query):
    es_query = {
        "retriever": {
            "standard": {
                "query": {
                    "knn": {
                        "field": "vector",
                        "num_candidates": 100,
                        "query_vector_builder": {
                            "text_embedding": {
                                "model_id": ".multilingual-e5-small_linux-x86_64",
                                "model_text": query
                            }
                        }
                    }
                }
            }
        },
        "size": 3
    }
    result = es_client.search(index=os.environ["ES_INDEX_NAME"], body=es_query)
    return result["hits"]["hits"]

def create_openai_prompt(results):
    context = ""
    for hit in results:
        inner_hit_path = f"{hit['_index']}.{index_source_fields.get(hit['_index'])[0]}"
        ## For semantic_text matches, we need to extract the text from the inner_hits
        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            context += '\n --- \n'.join(inner_hit['_source']['text'] for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits'])
        else:
            source_field = index_source_fields.get(hit["_index"])[1]
            hit_context = hit["_source"][source_field]
            context += f"{hit_context}\n"
    prompt = f"""
  Instructions:
  
  - You are an assistant for question-answering tasks.
  - Answer questions truthfully and factually using only the context presented.
  - If you don't know the answer, just say that you don't know, don't make up an answer.
  - You must always cite the document where the answer was extracted using inline academic citation style [], using the position.
  - Use markdown format for code examples.
  - You are correct, factual, precise, and reliable.
  
  Context:
  {context}
  
  """
    return prompt

def generate_openai_completion(user_prompt, question):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": user_prompt},
            {"role": "user", "content": question},
        ]
    )
    return response.choices[0].message.content


@app.route("/")
def welcome():
    return render_template('index.html', title='Chat App', message='Welcome to the chat!')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question =data.get('message')
    elasticsearch_results = get_elasticsearch_results(question)
    context_prompt = create_openai_prompt(elasticsearch_results)
    openai_completion = generate_openai_completion(context_prompt, question)
    print(openai_completion)
    
    return jsonify({'response': openai_completion})


if __name__ == '__main__':
    app.run(debug=True)