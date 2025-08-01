from django.shortcuts import render
import json
import requests
from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv()
def home(request):
    return render(request,'home.html')

def search(request):
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'name': request.POST.get('name'),
                'relationship': request.POST.get('relationship'),
                'gender': request.POST.get('qloo_gender'),
                'age': request.POST.get('qloo_age'),
                'hobbies': request.POST.get('hobbies'),
                'personality': request.POST.get('personality'),
                'dislikes': request.POST.get('dislikes'),
                'budget_min': request.POST.get('budget_min'),
                'budget_max': request.POST.get('budget_max'),
                'occasion': request.POST.get('occasion')
            }

            # Step 1: Call Qloo API
            qloo_params = {
                "filter.type": "urn:entity:brand",
                "signal.demographics.gender": form_data['gender'],
                "signal.demographics.age": form_data['age'],
                "filter.popularity.min": request.POST.get('popularity_min', '0.5'),
                "filter.popularity.max": request.POST.get('popularity_max', '1.0'),
                "bias.trends": request.POST.get('qloo_trends', 'medium'),
                "take": request.POST.get('qloo_results', '5')
            }

            # Step 1: Call Qloo API using your working code
            response = requests.get(
                url="https://hackathon.api.qloo.com/v2/insights",
                headers={"x-api-key": os.getenv('QLOO_API_KEY')},
                params=qloo_params
            )
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get("results", {}).get("entities", [])
                
                output = []
                for item in entities:
                    formatted = {
                        "name": item.get("name"),
                        "description": item.get("properties", {}).get("short_description"),
                        "tags": [tag.get("name") for tag in item.get("tags", [])],
                        "image": item.get("properties", {}).get("image", {}).get("url")
                    }
                    output.append(formatted)
                
                the_main_data = json.dumps(output, indent=2)
                print("Qloo data processed successfully:")
                print(the_main_data)
            else:
                the_main_data = "[]"
                print(f"Qloo API failed with status: {response.status_code}")
            
            # Step 2: Process with Groq
            print("About to call Groq API...")
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            
            prompt = f"""
            Generate personalized gift recommendations for:
            - Name: {form_data['name']}
            - Relationship: {form_data['relationship']}
            - Age/Gender: {form_data['age']}, {form_data['gender']}
            - Personality: {form_data['personality']}
            - Hobbies: {form_data['hobbies']}
            - Dislikes: {form_data['dislikes']}
            - Budget: ${form_data['budget_min']}-${form_data['budget_max']}
            - Occasion: {form_data['occasion']}

            Based on these brand insights: {the_main_data}

            Return JSON with this structure for each recommendation:
            {{
                "gift_name": "creative name",
                "description": "detailed description",
                "reason": "why it's a good match",
                "price_range": "$XX-XX",
                "image_url": "relevant image URL",
                "purchase_link": "simulated purchase URL"
            }}
            please always json, no matter what do not generate anything other than json
            """
            
            groq_response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                response_format={"type": "json_object"},
                temperature=0.7
            )
            print("Groq API call successful!")
            
            groq_content = groq_response.choices[0].message.content
            print("Raw Groq response:", groq_content)
            
            recommendations = json.loads(groq_content)
            print("Parsed recommendations:", recommendations)
            
            # Prepare context
            context = {
                'user_info': form_data,
                'recommendations': recommendations.get('gifts', []),
                'occasion': form_data['occasion']
            }
            print("About to render result.html...")
            return render(request, 'result.html', context)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return render(request, 'search.html', {'error': str(e)})
    
    return render(request, 'search.html')
def result(request):
    return render(request, 'result.html')